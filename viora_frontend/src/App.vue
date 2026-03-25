<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { Search, Home, Clapperboard, MonitorPlay, Bookmark, Play, Plus, User as UserIcon, Star, Flame, X, Loader2 } from 'lucide-vue-next';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

const heroMovies = ref([]);
const currentHeroIndex = ref(0);
const movieCategories = ref([]);
const isLoading = ref(true);
const isScrolled = ref(false);
let heroTimer = null;

// Search State
const isSearchOpen = ref(false);
const searchQuery = ref('');
const searchResults = ref([]);
const isSearching = ref(false);
let searchTimeout = null;

const API_KEY = import.meta.env.VITE_TMDB_API_KEY;
const BASE_URL = 'https://api.themoviedb.org/3';

// Helper Image Loader dengan wsrv.nl (WebP + Cache)
const getImageUrl = (path, width = 'w780') => {
  if (!path) return 'https://via.placeholder.com/300x450?text=No+Image';
  const tmdbUrl = `https://image.tmdb.org/t/p/${width}${path}`;
  return `https://wsrv.nl/?url=${encodeURIComponent(tmdbUrl)}&output=webp&q=80&n=-1`;
};

// Fungsi sakti buat ambil Logo PNG Transparan
const fetchLogo = async (id, type = 'movie') => {
  try {
    const res = await axios.get(`${BASE_URL}/${type}/${id}/images?api_key=${API_KEY}&include_image_language=en,null`);
    const logo = res.data.logos?.find(l => l.file_path.endsWith('.png')) || res.data.logos?.[0];
    return logo ? logo.file_path : null;
  } catch (e) { return null; }
};

// Fungsi untuk memperkaya data film dengan logo secara massal
const enrichMoviesWithLogos = async (movies) => {
  return Promise.all(movies.map(async (m) => {
    const logoPath = await fetchLogo(m.id, m.media_type || 'movie');
    return { ...m, logo_path: logoPath };
  }));
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

    movieCategories.value = await Promise.all(categoriesData.map(async (cat) => ({
      id: cat.id,
      title: cat.title,
      movies: await enrichMoviesWithLogos(cat.raw)
    })));

    startHeroCarousel();
  } catch (error) { 
    console.error(error); 
  } finally { 
    isLoading.value = false; 
  }
};

// Fitur Spotlight Search
const toggleSearch = () => {
  isSearchOpen.value = !isSearchOpen.value;
  if (isSearchOpen.value) {
    nextTick(() => document.getElementById('viora-search-input')?.focus());
  } else {
    searchQuery.value = '';
    searchResults.value = [];
  }
};

const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = [];
    return;
  }
  isSearching.value = true;
  try {
    const res = await axios.get(`${BASE_URL}/search/multi?api_key=${API_KEY}&query=${encodeURIComponent(searchQuery.value)}&include_adult=false`);
    // Filter out people, keep only movies and tv shows
    searchResults.value = res.data.results.filter(item => item.media_type === 'movie' || item.media_type === 'tv').slice(0, 6);
  } catch (error) {
    console.error(error);
  } finally {
    isSearching.value = false;
  }
};

const onSearchInput = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(performSearch, 500); // Debounce 500ms
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
  if (e.key === 'Escape' && isSearchOpen.value) toggleSearch();
};

const startHeroCarousel = () => {
  heroTimer = setInterval(() => {
    currentHeroIndex.value = (currentHeroIndex.value + 1) % heroMovies.value.length;
  }, 8000);
};

onMounted(() => {
  fetchAllData();
  window.addEventListener('scroll', handleScroll);
  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  window.removeEventListener('keydown', handleKeydown);
  if (heroTimer) clearInterval(heroTimer);
});
</script>

<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_20%_30%,rgba(59,130,246,0.08),transparent_40%)] text-white font-sans selection:bg-blue-500/30 overflow-x-hidden pb-32">
    
   <Transition name="fade">
      <div v-if="isSearchOpen" class="fixed inset-0 z-[100] bg-black/70  flex justify-center items-start pt-[12vh]" @click.self="toggleSearch">
        <div class="w-full max-w-2xl bg-[#18181b]/80  border border-white/10 rounded-2xl shadow-[0_20px_60px_-15px_rgba(0,0,0,1)] overflow-hidden flex flex-col mx-4 transform transition-all">
          
          <div class="flex items-center px-5 py-4 border-b border-white/10 bg-black/20">
            <Search class="w-6 h-6 text-gray-400 mr-4" />
            <input 
              id="viora-search-input" 
              v-model="searchQuery" 
              @input="onSearchInput" 
              placeholder="Search movies, series, or actors..." 
              class="flex-1 bg-transparent border-none outline-none text-xl text-white placeholder:text-gray-500 font-medium"
              autocomplete="off"
            />
            <button v-if="searchQuery" @click="searchQuery = ''; searchResults = []" class="p-1 mr-2 hover:bg-white/10 rounded-full transition-colors">
              <X class="w-5 h-5 text-gray-400" />
            </button>
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
              <div 
                v-for="item in searchResults" 
                :key="item.id" 
                class="flex items-center gap-4 p-3 hover:bg-white/5 rounded-xl cursor-pointer transition-colors group"
              >
                <div class="w-14 h-20 bg-white/5 rounded-md overflow-hidden flex-shrink-0 shadow-md">
                  <img :src="getImageUrl(item.poster_path || item.backdrop_path, 'w185')" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                </div>
                
                <div class="flex-1 min-w-0">
                  <h4 class="text-white font-bold text-lg leading-tight group-hover:text-blue-500 transition-colors truncate">
                    {{ item.title || item.name }}
                  </h4>
                  <div class="flex items-center gap-3 text-xs text-gray-400 mt-2 font-medium">
                    <span class="bg-white/10 px-2 py-0.5 rounded text-white tracking-wide">{{ item.media_type === 'tv' ? 'Series' : 'Movie' }}</span>
                    <span>{{ (item.release_date || item.first_air_date)?.substring(0,4) }}</span>
                    <span class="flex items-center gap-1 text-yellow-500 bg-yellow-500/10 px-1.5 py-0.5 rounded"><Star class="w-3 h-3 fill-current"/> {{ item.vote_average?.toFixed(1) }}</span>
                  </div>
                </div>
                
                <div class="w-10 h-10 rounded-full flex items-center justify-center group-hover:bg-white/10 transition-colors">
                  <Play class="w-5 h-5 text-gray-400 group-hover:text-white" />
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
    </Transition>

    <header 
      :class="[
        'fixed top-0 w-full z-40 flex items-center justify-between transition-all duration-900 px-6 lg:px-12',
        isScrolled ? 'backdrop-blur-sm py-3 border-b border-white/5 bg-black/20 shadow-2xl' : 'bg-transparent py-8'
      ]"
    >
      <h1 class="font-black tracking-tighter flex items-center cursor-pointer transition-all duration-600" :class="isScrolled ? 'text-2xl' : 'text-4xl'">
        <span class="text-white">V</span>
        <span class="overflow-hidden transition-all duration-500" :class="isScrolled ? 'max-w-0 opacity-0' : 'max-w-[120px] opacity-100'">IORA</span>
        <span class="text-blue-500">.</span>
      </h1>

      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-500 to-blue-400 p-[2px] cursor-pointer hover:scale-110 transition-transform shadow-lg shadow-blue-500/20">
        <div class="w-full h-full rounded-full bg-[#09090b] flex items-center justify-center">
           <UserIcon class="w-5 h-5" />
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
                <Button size="lg" class="bg-white text-black hover:bg-blue-500 hover:text-white font-black px-10 h-16 rounded-2xl transition-transform transition-opacity shadow-2xl">
                  <Play class="w-6 h-6 mr-2 fill-current" /> Play
                </Button>
                <Button size="lg" variant="outline" class="bg-white/10  border-white/20 hover:bg-white/20 h-16 px-10 rounded-2xl font-bold">
                  <Plus class="w-6 h-6 mr-2" /> My List
                </Button>
              </div>
            </div>
          </div>
        </transition-group>
      </section>

      <main class="relative z-20 -mt-20 space-y-10 pb-20">
        <section v-for="category in movieCategories" :key="category.id" class="pl-6 lg:pl-12">
          <h3 class="text-2xl font-black mb-8 tracking-tight flex items-center gap-3 ">
            <span class="w-1.5 h-8 bg-blue-500 rounded-full"></span>
            {{ category.title }}
          </h3>
          
          <div class="flex gap-6 overflow-x-auto hide-scrollbar pb-10 pt-4 scroll-smooth ">
            <div 
              v-for="movie in category.movies" 
              :key="movie.id"
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
              <div class="absolute inset-0 rounded-2xl pointer-events-none 
bg-gradient-to-t from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>

              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-transform transition-opacity duration-300">
                 <div class="w-14 h-14 bg-white/10  rounded-full flex items-center justify-center border border-white/30 transform scale-50 group-hover:scale-100 transition-transform">
                    <Play class="w-6 h-6 text-white fill-current" />
                 </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>

    <nav class="fixed bottom-10 left-1/2 -translate-x-1/2 z-50">
      <div class="flex items-center gap-2 px-4 py-3 bg-white/5 backdrop-blur-xl border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.4)]  border border-white/10 rounded-full shadow-lg ">
        <div class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Home class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-transform transition-opacity" />
        </div>
        
        <div @click="toggleSearch" class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Search 
            class="w-6 h-6 transition-transform transition-colors"
            :class="[
              isSearchOpen 
                ? 'text-blue-500' 
                : 'text-gray-400 group-hover:text-white',
              'group-hover:-translate-y-1'
            ]"
          />
        </div>
        
        <div class="w-px h-8 bg-white/10 mx-1"></div>
        <div class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Clapperboard class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-transform transition-opacity" />
        </div>
        <div class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <MonitorPlay class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-transform transition-opacity" />
        </div>
        <div class="p-3 rounded-full hover:bg-white/10 transition-transform transition-opacity cursor-pointer group">
          <Bookmark class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-transform transition-opacity" />
        </div>
      </div>
    </nav>
  </div>
</template>

<style scoped>
/* Transisi untuk banner utama */
.hero-fade-enter-active, .hero-fade-leave-active { transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1); }
.hero-fade-enter-from { opacity: 0; transform: translateY(20px); }
.hero-fade-leave-to { opacity: 0; transform: translateY(-20px); }

/* Transisi untuk Spotlight Overlay */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease, transform 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.98) translateY(-10px); }

.hide-scrollbar::-webkit-scrollbar { display: none; }
.hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>