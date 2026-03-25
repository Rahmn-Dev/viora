<script setup>
axios.defaults.baseURL = 'http://localhost:8000';

axios.interceptors.response.use(
  res => res,
  async (err) => {
    const status = err.response?.status;
    if (status === 401 && !err.config._retry) {
      err.config._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (!refresh) {
        handleLogout();
        return Promise.reject(err);
      }
      try {
        const res = await axios.post('/api/token/refresh/', { refresh: refresh });
        const newAccess = res.data.access;
        localStorage.setItem('access_token', newAccess);
        axios.defaults.headers.common['Authorization'] = `Bearer ${newAccess}`;
        err.config.headers['Authorization'] = `Bearer ${newAccess}`;
        return axios(err.config);
      } catch (e) {
        handleLogout(); 
      }
    }
    return Promise.reject(err);
  }
);

import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { Search, Home, Clapperboard, MonitorPlay, Bookmark, Play, Plus, User as UserIcon, Star, Flame, Check, X, Loader2, LogOut, Settings } from 'lucide-vue-next';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

const heroMovies = ref([]);
const currentHeroIndex = ref(0);
const movieCategories = ref([]);
const isLoading = ref(true);
const isScrolled = ref(false);
let heroTimer = null;

const isSearchOpen = ref(false);
const searchQuery = ref('');
const searchResults = ref([]);
const isSearching = ref(false);
let searchTimeout = null;

const isLoggedIn = ref(false);
const currentUser = ref({ username: '' });
const isLoginOpen = ref(false);
const isProfileOpen = ref(false);
const loginData = ref({ username: '', password: '' });
const isLoggingIn = ref(false);
const loginError = ref('');

const isPlayerOpen = ref(false);
const currentMedia = ref(null); 
const embedUrl = ref('');

const watchHistoryMovies = ref([]); 
const watchlistMovies = ref([]); 
const isWatchlistOpen = ref(false); 
const watchlist = ref(new Set()); 

const API_KEY = import.meta.env.VITE_TMDB_API_KEY;
// MENGAMBIL KEY WYZIE DARI .ENV
const WYZIE_API_KEY = import.meta.env.VITE_WYZIE_API_KEY; 
const BASE_URL = 'https://api.themoviedb.org/3';

const getImageUrl = (path, width = 'w780') => {
  if (!path) return 'https://via.placeholder.com/300x450?text=No+Image';
  const tmdbUrl = `https://image.tmdb.org/t/p/${width}${path}`;
  return `https://wsrv.nl/?url=${encodeURIComponent(tmdbUrl)}&output=webp&q=80&n=-1`;
};

const fetchLogo = async (id, type = 'movie') => {
  try {
    const res = await axios.get(`${BASE_URL}/${type}/${id}/images?api_key=${API_KEY}&include_image_language=en,null`);
    const logo = res.data.logos?.find(l => l.file_path.endsWith('.png')) || res.data.logos?.[0];
    return logo ? logo.file_path : null;
  } catch (e) { return null; }
};

const enrichMoviesWithLogos = async (movies) => {
  return Promise.all(movies.map(async (m) => {
    const logoPath = await fetchLogo(m.id, m.media_type || 'movie');
    return { ...m, logo_path: logoPath };
  }));
};

const fetchUserData = async () => {
  if (!isLoggedIn.value) return;
  try {
    const historyRes = await axios.get('/api/watch-history/');
    const historyData = historyRes.data;
    if (historyData.length > 0) {
      const historyDetails = await Promise.all(
        historyData.map(async (item) => {
          const tmdbRes = await axios.get(`${BASE_URL}/${item.media_type}/${item.tmdb_id}?api_key=${API_KEY}`);
          return { ...tmdbRes.data, media_type: item.media_type, progress_percentage: item.progress_percentage };
        })
      );
      watchHistoryMovies.value = await enrichMoviesWithLogos(historyDetails);
    }
  } catch (error) { console.error("❌ Failed to fetch history:", error); }
};

const handleRemoveHistory = async (movie) => {
  try {
    await axios.delete('/api/watch-history/', { data: { tmdb_id: movie.id, media_type: movie.media_type }});
    watchHistoryMovies.value = watchHistoryMovies.value.filter(m => m.id !== movie.id);
  } catch (err) { console.error("❌ Failed remove history", err); }
};

const fetchAllData = async () => {
  try {
    const [trending, topRated, action, animation] = await Promise.all([
      axios.get(`${BASE_URL}/trending/all/day?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/movie/top_rated?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/discover/movie?api_key=${API_KEY}&with_genres=28`),
      axios.get(`${BASE_URL}/discover/movie?api_key=${API_KEY}&with_genres=16`)
    ]);

    heroMovies.value = await enrichMoviesWithLogos(trending.data.results.slice(0, 5));
    const categoriesData = [
      { id: 1, title: 'Trending Now', raw: trending.data.results.slice(5, 15) },
      { id: 2, title: 'Top Rated Movies', raw: topRated.data.results.slice(0, 10) },
      { id: 3, title: 'Action Thriller', raw: action.data.results.slice(0, 10) },
      { id: 4, title: 'Animation Series', raw: animation.data.results.slice(0, 10) },
    ];
    movieCategories.value = await Promise.all(categoriesData.map(async (cat) => ({ id: cat.id, title: cat.title, movies: await enrichMoviesWithLogos(cat.raw) })));
    startHeroCarousel();
  } catch (error) { console.error(error); } finally { isLoading.value = false; }
};

const toggleSearch = () => {
  if (isLoginOpen.value) isLoginOpen.value = false;
  if (isProfileOpen.value) isProfileOpen.value = false;
  if (isWatchlistOpen.value) isWatchlistOpen.value = false;
  isSearchOpen.value = !isSearchOpen.value;
  if (isSearchOpen.value) nextTick(() => document.getElementById('viora-search-input')?.focus());
};

const toggleWatchlist = () => {
  checkLoginStatus()
  if (!isLoggedIn.value) { isLoginOpen.value = true; return; }
  if (isSearchOpen.value) isSearchOpen.value = false;
  if (isProfileOpen.value) isProfileOpen.value = false;
  isWatchlistOpen.value = !isWatchlistOpen.value;
};

const handleUserIconClick = () => {
  if (isSearchOpen.value) isSearchOpen.value = false;
  if (isWatchlistOpen.value) isWatchlistOpen.value = false;
  if (isLoggedIn.value) {
    isProfileOpen.value = !isProfileOpen.value;
    if (isLoginOpen.value) isLoginOpen.value = false;
  } else {
    isLoginOpen.value = !isLoginOpen.value;
    if (isProfileOpen.value) isProfileOpen.value = false;
  }
};

const handleWatchlistToggle = async (movie, type = null) => {
  if (!isLoggedIn.value) { isLoginOpen.value = true; return; }
  const mediaType = type || movie.media_type || 'movie';
  try {
    const res = await axios.post('/api/watchlist/toggle/', {
      tmdb_id: movie.id, media_type: mediaType, title: movie.title || movie.name,
      poster_path: movie.poster_path, backdrop_path: movie.backdrop_path,
      rating: movie.vote_average, year: (movie.release_date || movie.first_air_date)?.substring(0, 4)
    });
    if (res.data.status === "added") { watchlist.value.add(movie.id); } 
    else { watchlist.value.delete(movie.id); }
  } catch (err) { console.error("❌ Failed to update watchlist", err); }
};

const performSearch = async () => {
  if (!searchQuery.value.trim()) { searchResults.value = []; return; }
  isSearching.value = true;
  try {
    const res = await axios.get(`${BASE_URL}/search/multi?api_key=${API_KEY}&query=${encodeURIComponent(searchQuery.value)}&include_adult=false`);
    searchResults.value = res.data.results.filter(item => item.media_type === 'movie' || item.media_type === 'tv').slice(0, 6);
  } catch (error) { console.error(error); } finally { isSearching.value = false; }
};

const onSearchInput = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(performSearch, 500);
};

const fetchWatchlist = async () => {
  try {
    const res = await axios.get('/api/watchlist/');
    watchlist.value = new Set(res.data.map(item => item.id));
    watchlistMovies.value = res.data;
  } catch (err) { console.error("gagal ambil watchlist", err); }
};

const handleLogin = async () => {
  if (!loginData.value.username || !loginData.value.password) { loginError.value = 'Please fill in all fields.'; return; }
  isLoggingIn.value = true;
  loginError.value = '';
  try {
    const response = await axios.post('/api/login/', { username: loginData.value.username, password: loginData.value.password });
    const accessToken = response.data.access;
    const refreshToken = response.data.refresh;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    isLoggedIn.value = true;
    currentUser.value = { username: loginData.value.username };
    localStorage.setItem('viora_auth_status', 'true');
    localStorage.setItem('viora_auth_user', loginData.value.username);
    await fetchUserData();
    await fetchWatchlist();
    isLoginOpen.value = false;
    loginData.value = { username: '', password: '' };
  } catch (error) {
    console.error(error);
    loginError.value = error.response?.data?.detail || 'Login failed.';
  } finally { isLoggingIn.value = false; }
};

const handleLogout = () => {
  isLoggedIn.value = false;
  currentUser.value = { username: '' };
  isProfileOpen.value = false;
  isWatchlistOpen.value = false;
  watchHistoryMovies.value = [];
  watchlistMovies.value = [];
  watchlist.value.clear();
  localStorage.removeItem('viora_auth_status');
  localStorage.removeItem('viora_auth_user');
  localStorage.removeItem('access_token');
  delete axios.defaults.headers.common['Authorization'];
};

const checkLoginStatus = () => {
  const token = localStorage.getItem('access_token');
  const user = localStorage.getItem('viora_auth_user');
  if (token && user) {
    isLoggedIn.value = true;
    currentUser.value = { username: user };
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    fetchUserData();
    fetchWatchlist(); 
  }
};

// --- FUNGSI VIDEO PLAYER ---
const openPlayer = (movie) => {
  if (!isLoggedIn.value) { isLoginOpen.value = true; return; }
  const type = movie.media_type === 'tv' ? 'tv' : 'movie'; 
  currentMedia.value = movie;
  let startTime = 0;

  const history = watchHistoryMovies.value.find(m => m.id === movie.id);
  if (history && history.current_time_seconds) {
    startTime = Math.floor(history.current_time_seconds);
  }

  // MENYISIPKAN KEY WYZIE UNTUK SUBTITLE
  // Menggunakan fallback language: "id,en" agar ada opsi Indonesia, lalu Inggris
  if (type === 'movie') {
    embedUrl.value = `https://www.vidking.net/embed/movie/${movie.id}?autoPlay=true&t=${startTime}&lan=id,en&key=${WYZIE_API_KEY}`;
  } else {
    embedUrl.value = `https://www.vidking.net/embed/tv/${movie.id}/1/1?autoPlay=true&t=${startTime}&lan=id,en&key=${WYZIE_API_KEY}`;
  }

  isPlayerOpen.value = true;
  if(heroTimer) clearInterval(heroTimer); 
};

const closePlayer = () => {
  isPlayerOpen.value = false;
  embedUrl.value = '';
  currentMedia.value = null;
  startHeroCarousel(); 
  fetchUserData();
};

let lastSaveTime = 0;
const handlePlayerMessage = async (event) => {
  try {
    const message = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
    if (message && message.type === 'PLAYER_EVENT') {
       const { event: playerEvent, progress, currentTime, duration, id, mediaType, season, episode } = message.data;
       if (!isLoggedIn.value) return;
       const now = Date.now();
       if (playerEvent === 'pause' || playerEvent === 'ended' || (playerEvent === 'timeupdate' && now - lastSaveTime > 3000)) {
         lastSaveTime = now; 
         try {
           await axios.post('/api/watch-history/', {
              tmdb_id: id, media_type: mediaType, season: season || null, episode: episode || null,
              progress_percentage: progress, current_time_seconds: currentTime, total_duration: duration,
              is_finished: playerEvent === 'ended'
            });
            await fetchUserData()
         } catch (e) { console.error('Failed to save progress', e); }
       }
    }
  } catch (e) {}
};

let ticking = false;
const handleScroll = () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      isScrolled.value = window.scrollY > 50;
      ticking = false;
    });
    ticking = true;
  }
};

const handleKeydown = (e) => {
  if (e.key === 'Escape') {
    if (isPlayerOpen.value) closePlayer();
    if (isSearchOpen.value) toggleSearch();
    if (isWatchlistOpen.value) toggleWatchlist();
    if (isLoginOpen.value) isLoginOpen.value = false;
    if (isProfileOpen.value) isProfileOpen.value = false;
  }
};

const startHeroCarousel = () => {
  if(heroTimer) clearInterval(heroTimer);
  heroTimer = setInterval(() => {
    currentHeroIndex.value = (currentHeroIndex.value + 1) % heroMovies.value.length;
  }, 8000);
};

onMounted(() => {
  checkLoginStatus();
  fetchAllData();
  window.addEventListener('scroll', handleScroll);
  window.addEventListener('keydown', handleKeydown);
  window.addEventListener('message', handlePlayerMessage); 
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  window.removeEventListener('keydown', handleKeydown);
  window.removeEventListener('message', handlePlayerMessage);
  if (heroTimer) clearInterval(heroTimer);
});
</script>

<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_20%_30%,rgba(59,130,246,0.08),transparent_40%)] text-white font-sans selection:bg-blue-500/30 overflow-x-hidden pb-32">
    
 <Transition name="fade">
      <div v-if="isPlayerOpen" class="fixed inset-0 z-[200] bg-black flex flex-col items-center justify-center">
        
        <div class="absolute top-0 left-0 w-full p-6 flex justify-between items-start bg-gradient-to-b from-black/80 to-transparent z-10 pointer-events-none">
           
           <div>
              <img 
                v-if="currentMedia?.logo_path" 
                :src="getImageUrl(currentMedia.logo_path, 'w300')" 
                class="max-h-[35px] md:max-h-[45px] max-w-[200px] md:max-w-[300px] object-contain drop-shadow-lg origin-left" 
                :alt="currentMedia?.title || currentMedia?.name"
              />
              <h2 v-else class="text-xl md:text-2xl font-black uppercase italic tracking-tighter drop-shadow-md text-white">
                {{ currentMedia?.title || currentMedia?.name }}
              </h2>
           </div>

           <div class="pointer-events-auto group w-200 h-33 flex justify-end items-start -mt-2 -mr-1">
              <button @click="closePlayer" class="opacity-0 group-hover:opacity-100 p-2 bg-white/10 hover:bg-red-600 rounded-full backdrop-blur-md transition-all duration-300 text-white shadow-xl cursor-pointer">
                 <X class="w-10 h-10" />
              </button>
           </div>

        </div>

        <div v-if="embedUrl" class="w-full h-full">
            <iframe :src="embedUrl" width="100%" height="100%" frameborder="0" allowfullscreen class="w-full h-full"></iframe>
        </div>

      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isWatchlistOpen" class="fixed inset-0 z-[100] bg-black/90 overflow-y-auto backdrop-blur-xl" @click.self="toggleWatchlist">
        <div class="min-h-screen p-6 lg:p-12 pt-24 relative max-w-7xl mx-auto">
          <button @click="toggleWatchlist" class="fixed top-8 right-8 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors z-50 shadow-xl">
            <X class="w-6 h-6 text-white" />
          </button>
          
          <h2 class="text-4xl font-black mb-10 tracking-tight   flex items-center gap-4">
            <span class="w-2 h-10 bg-blue-500 rounded-full"></span>
            My <span class="text-blue-500">Watchlist</span>
          </h2>

          <div v-if="watchlistMovies.length === 0" class="flex flex-col items-center justify-center mt-32 text-gray-400">
            <Bookmark class="w-16 h-16 mb-4 opacity-50" />
            <p class="text-xl font-medium">Your watchlist is empty.</p>
            <p class="text-sm mt-2">Save movies and series to watch them later.</p>
          </div>

          <div v-else class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            <div 
              v-for="movie in watchlistMovies" :key="movie.id"
              class="relative aspect-video md:aspect-[2/3] rounded-2xl overflow-hidden bg-[#18181b] transition-transform transition-opacity duration-500 hover:scale-105 hover:z-40 hover:shadow-[0_0_60px_rgba(59,130,246,0.18)] transform-gpu group ring-1 ring-white/5 cursor-pointer"
            >
              <img :src="getImageUrl(movie.poster_path || movie.backdrop_path, 'w500')" class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-transform transition-opacity duration-700 group-hover:scale-110" />

              <div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent p-5 flex flex-col justify-end">
                <div class="mb-2">
                  <img v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w300')" class="max-w-[120px] max-h-[40px] object-contain drop-shadow-lg transition-transform group-hover:scale-110 origin-left" />
                  <h4 v-else class="text-sm md:text-base font-black uppercase italic tracking-tighter line-clamp-2 drop-shadow-md">{{ movie.title || movie.name }}</h4>
                </div>
              </div>

              <div class="absolute top-3 right-3 z-20">
                <button @click.stop="handleWatchlistToggle(movie)" class="p-2 bg-black/60 hover:bg-red-600/80 backdrop-blur-md rounded-full transition-colors border border-white/20">
                  <Check v-if="watchlist.has(movie.id)" class="w-4 h-4 text-green-400" />
                </button>
              </div>

              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-transform transition-opacity duration-300" @click="openPlayer(movie)">
                 <div class="w-12 h-12 bg-white/10 rounded-full flex items-center justify-center border border-white/30 transform scale-50 group-hover:scale-100 transition-transform">
                    <Play class="w-5 h-5 text-white fill-current" />
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isSearchOpen" class="fixed inset-0 z-[100] bg-black/70 flex justify-center items-start pt-[12vh]" @click.self="toggleSearch">
        <div class="w-full max-w-2xl bg-[#18181b]/80 border border-white/10 rounded-2xl shadow-[0_20px_60px_-15px_rgba(0,0,0,1)] overflow-hidden flex flex-col mx-4 transform transition-all backdrop-blur-xl">
          <div class="flex items-center px-5 py-4 border-b border-white/10 bg-black/20">
            <Search class="w-6 h-6 text-gray-400 mr-4" />
            <input id="viora-search-input" v-model="searchQuery" @input="onSearchInput" placeholder="Search movies, series, or actors..." class="flex-1 bg-transparent border-none outline-none text-xl text-white placeholder:text-gray-500 font-medium" autocomplete="off" />
            <button v-if="searchQuery" @click="searchQuery = ''; searchResults = []" class="p-1 mr-2 hover:bg-white/10 rounded-full transition-colors"><X class="w-5 h-5 text-gray-400" /></button>
            <div class="px-2 py-1 bg-white/10 rounded text-[10px] font-bold text-gray-400 tracking-widest uppercase hidden md:block">ESC</div>
          </div>

          <div v-if="searchQuery" class="max-h-[60vh] overflow-y-auto hide-scrollbar p-2">
            <div v-if="isSearching" class="p-10 flex flex-col items-center justify-center gap-3">
              <Loader2 class="w-8 h-8 animate-spin text-blue-500" />
              <span class="text-sm text-gray-400 font-medium animate-pulse">Searching the universe...</span>
            </div>
            <div v-else-if="searchResults.length === 0" class="p-10 text-center flex flex-col items-center justify-center">
              <Search class="w-12 h-12 text-gray-600 mb-3" />
              <p class="text-gray-400 font-medium">No results found for "<span class="text-white">{{ searchQuery }}</span>"</p>
            </div>
            <div v-else class="space-y-1 p-1">
              <div v-for="item in searchResults" :key="item.id" @click="openPlayer(item)" class="flex items-center gap-4 p-3 hover:bg-white/5 rounded-xl cursor-pointer transition-colors group">
                <div class="w-14 h-20 bg-white/5 rounded-md overflow-hidden flex-shrink-0 shadow-md">
                  <img :src="getImageUrl(item.poster_path || item.backdrop_path, 'w185')" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                </div>
                <div class="flex-1 min-w-0">
                  <h4 class="text-white font-bold text-lg leading-tight group-hover:text-blue-500 transition-colors truncate">{{ item.title || item.name }}</h4>
                  <div class="flex items-center gap-3 text-xs text-gray-400 mt-2 font-medium">
                    <span class="bg-white/10 px-2 py-0.5 rounded text-white tracking-wide">{{ item.media_type === 'tv' ? 'Series' : 'Movie' }}</span>
                    <span>{{ (item.release_date || item.first_air_date)?.substring(0,4) }}</span>
                    <span class="flex items-center gap-1 text-yellow-500 bg-yellow-500/10 px-1.5 py-0.5 rounded"><Star class="w-3 h-3 fill-current"/> {{ item.vote_average?.toFixed(1) }}</span>
                  </div>
                   
                </div>
                
                <div class="w-10 h-10 rounded-full flex items-center justify-center group-hover:bg-white/10 transition-colors">
                  <Play class="w-5 h-5 text-gray-400 group-hover:text-white" />
                </div>
                  <button 
                  @click.stop="handleWatchlistToggle(item, item.media_type)"
                  class="w-10 h-10 rounded-full flex items-center justify-center bg-white/5 hover:bg-blue-500/20 transition"
                >
                  <Check v-if="watchlist.has(item.id)" class="w-4 h-4 text-green-400" />
                  <Plus v-else class="w-4 h-4 text-white" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isLoginOpen" class="fixed inset-0 z-[100] bg-black/70 flex justify-center items-center p-4" @click.self="isLoginOpen = false">
        <div class="w-full max-w-md bg-[#2b2b30]/40 border border-white/10 rounded-[2rem] shadow-[0_20px_60px_-15px_rgba(0,0,0,1)] p-8 transform transition-all relative backdrop-blur-sm">
          <button @click="isLoginOpen = false" class="absolute top-6 right-6 p-2 hover:bg-white/10 rounded-full transition-colors"><X class="w-5 h-5 text-gray-400" /></button>
          <div class="text-center mb-8">
            <div class="w-16 h-16 rounded-full bg-gradient-to-tr from-blue-500 to-blue-400 p-[2px] mx-auto mb-4 shadow-lg shadow-blue-500/20">
              <div class="w-full h-full rounded-full bg-[#09090b] flex items-center justify-center"><UserIcon class="w-8 h-8 text-white" /></div>
            </div>
            <h2 class="text-3xl font-black tracking-tighter text-white">Welcome Back</h2>
            <p class="text-sm text-gray-400 mt-1">Sign in to your Viora account</p>
          </div>
          <form @submit.prevent="handleLogin" class="space-y-5">
            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Username</label>
              <input id="viora-username-input" v-model="loginData.username" type="text" class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" placeholder="Enter your username" required />
            </div>
            <div>
              <div class="flex items-center justify-between mb-2">
                <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider">Password</label>
                <a href="#" class="text-xs text-blue-500 hover:text-blue-400 font-medium">Forgot?</a>
              </div>
              <input v-model="loginData.password" type="password" class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-gray-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" placeholder="••••••••" required />
            </div>
            <div v-if="loginError" class="text-red-400 text-sm font-medium text-center bg-red-500/10 py-3 rounded-xl border border-red-500/20">{{ loginError }}</div>
            <Button type="submit" :disabled="isLoggingIn" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold h-14 rounded-xl transition-all shadow-lg shadow-blue-600/20 mt-2 flex justify-center items-center">
              <Loader2 v-if="isLoggingIn" class="w-5 h-5 animate-spin mr-2" />
              {{ isLoggingIn ? 'Authenticating...' : 'Sign In' }}
            </Button>
          </form>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isProfileOpen" class="fixed inset-0 z-[95] bg-transparent" @click.self="isProfileOpen = false">
        <div class="absolute top-[80px] right-6 lg:right-12 w-64 bg-[#18181b]/90 border border-white/10 rounded-2xl shadow-[0_20px_40px_-10px_rgba(0,0,0,0.8)] p-2 transform transition-all backdrop-blur-2xl">
          <div class="flex items-center gap-3 p-3 mb-2 border-b border-white/10">
            <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-blue-400 p-[2px] shadow-sm">
              <div class="w-full h-full rounded-full bg-[#09090b] flex items-center justify-center font-bold text-sm">{{ currentUser.username.charAt(0).toUpperCase() }}</div>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-white font-bold text-sm truncate">@{{ currentUser.username }}</h4>
              <p class="text-xs text-blue-400 font-medium">Premium Member</p>
            </div>
          </div>
          <div class="space-y-1">
             <button class="w-full flex items-center gap-3 p-2.5 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/10 rounded-xl transition-colors text-left"><Settings class="w-4 h-4 text-gray-400" /> Account Settings</button>
            <button @click="handleLogout" class="w-full flex items-center gap-3 p-2.5 text-sm font-bold text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-xl transition-colors text-left mt-1"><LogOut class="w-4 h-4" /> Log Out</button>
          </div>
        </div>
      </div>
    </Transition>

    <header :class="['fixed top-0 w-full z-40 flex items-center justify-between transition-all duration-700 px-6 lg:px-12', isScrolled ? 'backdrop-blur-sm py-3 border-b border-white/5 bg-black/20 shadow-2xl' : 'bg-transparent py-8']">
      <h1 class="font-black tracking-tighter flex items-center cursor-pointer transition-all duration-500" :class="isScrolled ? 'text-2xl' : 'text-4xl'">
        <span class="text-white">V</span>
        <span class="overflow-hidden transition-all duration-500" :class="isScrolled ? 'max-w-0 opacity-0' : 'max-w-[120px] opacity-100'">IORA</span>
        <span class="text-blue-500">.</span>
      </h1>
      <div @click="handleUserIconClick" class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-blue-400 p-[2px] cursor-pointer hover:scale-110 transition-transform shadow-lg shadow-blue-500/20 z-[96]">
        <div class="w-full h-full rounded-full bg-[#09090b] flex items-center justify-center">
           <span v-if="isLoggedIn" class="font-bold text-sm text-white">{{ currentUser.username.charAt(0).toUpperCase() }}</span>
           <UserIcon v-else class="w-5 h-5" />
        </div>
      </div>
    </header>

    <div v-if="isLoading" class="p-12 pt-32 space-y-8">
      <Skeleton class="w-full h-[80vh] rounded-3xl bg-white/5 animate-pulse" />
      <div class="flex gap-4 overflow-hidden">
        <Skeleton class="min-w-[350px] h-48 rounded-xl bg-white/5" v-for="i in 4" :key="i"/>
      </div>
    </div>

    <div v-else>
      <section class="relative w-full h-[90vh] lg:h-[100vh] overflow-hidden bg-black">
        <transition-group name="hero-fade">
          <div v-for="(movie, index) in heroMovies" :key="movie.id" v-show="index === currentHeroIndex" class="absolute inset-0">
            <img :src="getImageUrl(movie.backdrop_path, 'original')" class="w-full h-full object-cover opacity-60 scale-100 transition-transform duration-[10s]" :class="index === currentHeroIndex ? 'scale-110' : 'scale-100'" />
            
            <div class="absolute inset-0 bg-gradient-to-t from-[#09090b] via-[#0b1220]/30 to-transparent"></div>
            <div class="absolute inset-0 bg-gradient-to-r from-[#09090b] via-[#0b1220]/50 to-transparent"></div>

            <div class="absolute bottom-[15%] left-6 lg:left-12 max-w-2xl space-y-8 z-10">
              <div class="space-y-6">
                <div class="flex items-center gap-3">
                   <div class="flex items-center bg-[#f5c518] text-black px-2 py-0.5 rounded font-black text-[10px]">IMDb {{ movie.vote_average.toFixed(1) }}</div>
                   <span class="text-blue-500 font-bold text-[12px] uppercase tracking-[0.3em]">Viora Originals</span>
                </div>

                <img v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w500')" class="max-w-[300px] md:max-w-[480px] max-h-[160px] object-contain drop-shadow-lg" />
                <h2 v-else class="text-5xl lg:text-7xl font-black uppercase italic tracking-tighter">{{ movie.title || movie.name }}</h2>
              </div>

              <p class="text-gray-300 text-lg line-clamp-3 max-w-xl font-medium drop-shadow-md leading-relaxed">
                {{ movie.overview }}
              </p>

              <div class="flex items-center gap-4">
                <Button @click="openPlayer(movie)" size="lg" class="bg-white text-black hover:bg-blue-500 hover:text-white font-black px-10 h-16 rounded-2xl transition-transform transition-opacity shadow-2xl">
                  <Play class="w-6 h-6 mr-2 fill-current" /> Play
                </Button>
                <Button @click="handleWatchlistToggle(movie, movie.media_type)" size="lg" variant="outline" class="bg-white/10 border-white/20 hover:bg-white/20 h-16 px-10 rounded-2xl font-bold transition-all w-[200px]">
                  <template v-if="watchlist.has(movie.id)"><Check class="w-6 h-6 mr-2 text-green-400" /> Added</template>
                  <template v-else><Plus class="w-6 h-6 mr-2" /> My List</template>
                </Button>
              </div>
            </div>
          </div>
        </transition-group>
      </section>

      <main class="relative z-20 -mt-20 space-y-10 pb-20">
        
       <section v-if="isLoggedIn && watchHistoryMovies.length > 0" class="pl-6 lg:pl-12 pt-4">
          <h3 class="text-2xl font-black mb-8 tracking-tight flex items-center gap-3">
            <span class="w-1.5 h-8 bg-blue-500 rounded-full"></span> Continue Watching
          </h3>

          <div class="flex gap-6 overflow-x-auto hide-scrollbar pb-10 pt-4">
            
            <div 
              v-for="movie in watchHistoryMovies" 
              :key="movie.id"
              @click="openPlayer(movie)"
              class="relative flex-none w-[300px] md:w-[390px] aspect-video rounded-2xl overflow-hidden bg-[#18181b] group cursor-pointer transition-all hover:scale-110 hover:-translate-y-2 hover:z-40"
            >

              <img 
                :src="getImageUrl(movie.backdrop_path, 'w780')" 
                class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition duration-700 group-hover:scale-105" 
              />

              <div class="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent p-5 flex flex-col justify-end">
                
                <div class="mb-2">
                  <img v-if="movie.logo_path" 
                    :src="getImageUrl(movie.logo_path, 'w300')" 
                    class="max-w-[140px] max-h-[45px] object-contain" 
                  />
                  <h4 v-else class="text-sm font-black line-clamp-1">
                    {{ movie.title || movie.name }}
                  </h4>
                </div>

                <div class="flex items-center gap-3 text-[10px] font-black text-gray-400 mt-1 opacity-0 group-hover:opacity-100 transition-transform transition-opacity duration-500 translate-y-2 group-hover:translate-y-0">
                  <div class="bg-[#f5c518] text-black px-1.5 py-0.5 rounded">
                    IMDb {{ movie.vote_average?.toFixed(1) }}
                  </div>
                  <span>
                    {{ (movie.release_date || movie.first_air_date)?.substring(0,4) }}
                  </span>
                  <div class="bg-[#E97451]/90 text-white px-2 py-0.5 rounded-md flex items-center gap-1 text-[11px]">
                    <Flame class="w-3 h-3" />
                    <span>{{ movie.vote_count }}</span>
                  </div>
                </div>

              </div>

              <div class="absolute bottom-0 left-0 w-full h-1.5 bg-gray-800/80">
                <div 
                  class="h-full bg-blue-500"
                  :style="{ width: (movie.progress_percentage || 0) + '%' }"
                ></div>
              </div>

              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100">
                <div class="w-14 h-14 bg-white/10 rounded-full flex items-center justify-center border border-white/30">
                  <Play class="w-6 h-6 text-white fill-current" />
                </div>
              </div>

              <div class="absolute top-3 right-12 z-20">
                <button 
                  @click.stop="handleWatchlistToggle(movie, movie.media_type)"
                  class="p-2 bg-black/60 hover:bg-blue-500/60 rounded-full border border-white/20"
                >
                  <Check v-if="watchlist.has(movie.id)" class="w-4 h-4 text-green-400" />
                  <Plus v-else class="w-4 h-4 text-white" />
                </button>
              </div>

              <div class="absolute top-3 right-3 z-20">
                <button 
                  @click.stop="handleRemoveHistory(movie)"
                  class="p-2 bg-black/60 hover:bg-red-600 rounded-full border border-white/20"
                >
                  <X class="w-4 h-4 text-white" />
                </button>
              </div>

            </div>

          </div>
        </section>

        <section v-for="category in movieCategories" :key="category.id" class="pl-6 lg:pl-12">
          <h3 class="text-2xl font-black mb-8 tracking-tight flex items-center gap-3 ">
            <span class="w-1.5 h-8 bg-blue-500 rounded-full"></span> {{ category.title }}
          </h3>
          
          <div class="flex gap-6 overflow-x-auto hide-scrollbar pb-10 pt-4 scroll-smooth hover:shadow-[inset_0_-20px_40px_rgba(59,130,246,0.08)] transition-shadow duration-500" style="padding-bottom: 20px; padding-top: 20px;">
            <div 
              v-for="movie in category.movies" :key="movie.id" @click="openPlayer(movie)"
              class="relative flex-none w-[300px] md:w-[390px] aspect-video rounded-2xl overflow-hidden bg-[#18181b] transition-transform transition-opacity duration-500 hover:scale-110 hover:-translate-y-2 hover:z-40 hover:shadow-[0_0_60px_rgba(59,130,246,0.18)] transform-gpu group ring-1 ring-white/5 cursor-pointer"
            >
              <img :src="getImageUrl(movie.backdrop_path, 'w780')" class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-transform transition-opacity duration-700 group-hover:scale-105" />

              <div class="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent p-5 flex flex-col justify-end">
                <div class="mb-2">
                  <img v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w300')" class="max-w-[140px] max-h-[45px] object-contain drop-shadow-lg transition-transform group-hover:scale-110 origin-left" />
                  <h4 v-else class="text-sm md:text-base font-black uppercase italic tracking-tighter line-clamp-1">{{ movie.title || movie.name }}</h4>
                </div>

                <div class="flex items-center gap-3 text-[10px] font-black text-gray-400 mt-1 opacity-0 group-hover:opacity-100 transition-transform transition-opacity duration-500 translate-y-2 group-hover:translate-y-0">
                   <div class="bg-[#f5c518] text-black px-1.5 py-0.5 rounded ">IMDb {{ movie.vote_average.toFixed(1) }}</div>
                   <span class="text-white-600">{{ (movie.release_date || movie.first_air_date)?.substring(0,4) }}</span>
                   <div class="bg-[#E97451]/90 text-white px-2 py-0.5 rounded-md flex items-center gap-1 text-[11px] font-bold ">
                      <Flame class="w-3 h-3 opacity-80" />
                      <span>{{ movie.vote_count }}</span>
                    </div>
                </div>
              </div>
              <div class="absolute inset-0 rounded-2xl pointer-events-none bg-gradient-to-t from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-transform transition-opacity duration-300">
                 <div class="w-14 h-14 bg-white/10  rounded-full flex items-center justify-center border border-white/30 transform scale-50 group-hover:scale-100 transition-transform">
                    <Play class="w-6 h-6 text-white fill-current" />
                 </div>
              </div>
              <div class="absolute top-3 right-3 z-20">
                  <button 
                    @click.stop="handleWatchlistToggle(movie, movie.media_type)"
                    class="p-2 bg-black/60 hover:bg-blue-500/60 backdrop-blur-md rounded-full transition border border-white/20"
                  >
                    <Check v-if="watchlist.has(movie.id)" class="w-4 h-4 text-green-400" />
                    <Plus v-else class="w-4 h-4 text-white" />
                  </button>
                </div>
            </div>
          </div>
        </section>
      </main>
    </div>

    <nav class="fixed bottom-10 left-1/2 -translate-x-1/2 z-50">
      <div class="flex items-center gap-2 px-4 py-3 bg-white/5 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]  rounded-full ">
        <div class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Home class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-transform transition-opacity" />
        </div>
        
        <div @click="toggleSearch" class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Search class="w-6 h-6 transition-transform transition-colors" :class="[isSearchOpen ? 'text-blue-500 drop-shadow-[0_0_6px_rgba(59,130,246,0.6)]' : 'text-gray-400 group-hover:text-white', 'group-hover:-translate-y-1']" />
        </div>
        
        <div class="w-px h-8 bg-white/10 mx-1"></div>
        <div class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Clapperboard class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-transform transition-opacity" />
        </div>
        <div class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <MonitorPlay class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-transform transition-opacity" />
        </div>
        
        <div @click="toggleWatchlist" class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Bookmark class="w-6 h-6 transition-transform transition-colors" :class="[isWatchlistOpen ? 'text-blue-500 drop-shadow-[0_0_6px_rgba(59,130,246,0.6)]' : 'text-gray-400 group-hover:text-white', 'group-hover:-translate-y-1']" />
        </div>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.hero-fade-enter-active, .hero-fade-leave-active { transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1); }
.hero-fade-enter-from { opacity: 0; transform: translateY(20px); }
.hero-fade-leave-to { opacity: 0; transform: translateY(-20px); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.98) translateY(-5px); }

.hide-scrollbar::-webkit-scrollbar { height: 6px; }
.hide-scrollbar::-webkit-scrollbar-track { background: transparent; }
.hide-scrollbar::-webkit-scrollbar-thumb { background: rgba(59,130,246,0.3); border-radius: 999px; transition: all 0.3s ease; }
.hide-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(59,130,246,0.7); }
</style>