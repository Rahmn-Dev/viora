<script setup>

import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue';
import { Search, Home, Clapperboard, MonitorPlay, Bookmark, Play, Heart, Plus, User as UserIcon, Star, Flame, Check, X, Loader2, LogOut, Settings, Info, Filter, Tv, Film, PlayCircle, RadioTower, Eye, EyeOff, Sparkles, Layers, Server, ChevronDown, Menu, Maximize, Minimize, Lock } from 'lucide-vue-next';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import Lenis from 'lenis';

// Instance khusus untuk request ke backend Django kita
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:1234',
  withCredentials: true,  // kirim session cookie di setiap request ke backend
});

// Simpan CSRF token di memory untuk dikirim ulang
let currentCsrfToken = '';

// Interceptor Request: Masukkan CSRF Token ke header
api.interceptors.request.use(config => {
  if (currentCsrfToken) {
    config.headers['X-CSRFToken'] = currentCsrfToken;
  } else {
    // Fallback baca cookie (berguna saat local dev)
    const match = document.cookie.match(/(^|;\\s*)csrftoken=([^;]*)/);
    if (match) {
      config.headers['X-CSRFToken'] = match[2];
    }
  }
  return config;
});

// Interceptor Response: Tangkap CSRF Token baru dari backend
api.interceptors.response.use(
  res => {
    if (res.data && res.data.csrf_token) {
      currentCsrfToken = res.data.csrf_token;
    }
    return res;
  },
  (err) => {
    if (err.response?.data?.csrf_token) {
      currentCsrfToken = err.response.data.csrf_token;
    }
    if (err.response?.status === 401 && !err.config?.url?.includes('/api/me/')) {
      handleLogout();
    }
    return Promise.reject(err);
  }
);


let lenis;

const mouseX = ref(0)
const mouseY = ref(0)
const isHoveringHeroCard = ref(false);
let heroCardAutoScrollTimer = null;

const hasShownAutoLogin = ref(false);
const activeIndex = ref(0)
const hoverIndex = ref(null)
const isAnimating = ref(false)
const navRefs = ref([])
const magneticOffset = ref({ x: 0, y: 0 })
const magneticOffsets = ref({})
const activeMagnetIndex = ref(null)
const activeMagnet = ref(null)
const kidsZoneMovie = ref(null);

const resetMagnet = () => {
  magneticOffset.value = { x: 0, y: 0 }
  activeMagnet.value = null
}
const startHeroCardAutoScroll = () => {
  if (heroCardAutoScrollTimer) clearInterval(heroCardAutoScrollTimer);
  
  heroCardAutoScrollTimer = setInterval(() => {
    if (isHoveringHeroCard.value) return; 

    const containers = document.querySelectorAll('.hero-card-carousel');
    containers.forEach(container => {
      const firstChild = container.children[0];
      if (!firstChild) return;

      const scrollAmount = firstChild.offsetWidth + 24; 
      const isAtEnd = container.scrollLeft + container.clientWidth >= container.scrollWidth - 10;

      if (isAtEnd) {
        container.scrollTo({ left: 0, behavior: 'smooth' });
      } else {
        container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
      }
    });
  }, 4000); 
};

const sliderStyle = computed(() => {
  const index = hoverIndex.value ?? activeIndex.value
  const isHovering = hoverIndex.value !== null

  if (isAnimating.value) {
    return {
      transform: `translateX(${index * 56}px) scaleX(2) scaleY(0.2)`,
      borderRadius: '15px',
      boxShadow: '0 0 20px rgba(255, 255, 255, 2)' 
    }
  }

  return {
    transform: `translateX(${index * 56}px) scaleX(${isHovering ? 1 : 0.9}) scaleY(0.8)`,
    borderRadius: '20px',
    boxShadow: '0 0 15px rgba(255, 255, 255, 1)' 
  }
})

const glassTransform = computed(() => {
  const rotateX = mouseY.value * -5
  const rotateY = mouseX.value * 5
  const translateX = mouseX.value * 10
  const translateY = mouseY.value * 10

  return {
    transform: `
      perspective(1000px)
      rotateX(${rotateX}deg)
      rotateY(${rotateY}deg)
      translateX(${translateX}px)
      translateY(${translateY}px)
    `
  }
})

let _navMagnetRafId = null;
const handleNavMagnet = (e, index) => {
  if (_navMagnetRafId) return;
  const target = e.currentTarget;
  const clientX = e.clientX;
  const clientY = e.clientY;
  _navMagnetRafId = requestAnimationFrame(() => {
    const rect = target.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    magneticOffsets.value[index] = { x: (x - centerX) * 0.40, y: (y - centerY) * 0.40 };
    activeMagnetIndex.value = index;
    _navMagnetRafId = null;
  });
};

const resetNavMagnet = (index) => {
  if (_navMagnetRafId) {
    cancelAnimationFrame(_navMagnetRafId);
    _navMagnetRafId = null;
  }
  magneticOffsets.value[index] = { x: 0, y: 0 };
  activeMagnetIndex.value = null;
};

let _magnetMoveRafId = null;
const handleMagnetMove = (e, key) => {
  if (_magnetMoveRafId) return;
  const target = e.currentTarget;
  const clientX = e.clientX;
  const clientY = e.clientY;
  _magnetMoveRafId = requestAnimationFrame(() => {
    const rect = target.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    magneticOffset.value = { x: (x - centerX) * 0.2, y: (y - centerY) * 0.2 };
    activeMagnet.value = key;
    _magnetMoveRafId = null;
  });
};

let _mouseMoveRafId = null;
const handleMouseMove = (e) => {
  if (_mouseMoveRafId) return; // skip if a frame is already queued
  _mouseMoveRafId = requestAnimationFrame(() => {
    const x = (e.clientX / window.innerWidth - 0.5) * 2
    const y = (e.clientY / window.innerHeight - 0.5) * 2
    mouseX.value = x
    mouseY.value = y
    _mouseMoveRafId = null;
  });
}

const heroMovies = ref([]);
const currentHeroIndex = ref(0);
const movieCategories = ref([]);
const kidsZoneMovies = ref([]); 
const kidsCategories = ref([]); 
const upcomingMovies = ref([]);
const isLoading = ref(true);
const isScrolled = ref(false);
let heroTimer = null;

const selectedStudio = ref(null);
const studioMovies = ref([]);
const isFetchingStudio = ref(false);
const isStudiosExpanded = ref(false);
const vioraProgress = ref(0);

const getLetterProgress = (idx, total = 6) => {
  const p = vioraProgress.value;
  const start = (idx / total) * 0.55;
  const duration = 0.45;
  const itemP = (p - start) / duration;
  return Math.min(1, Math.max(0, itemP));
};

const studiosList = ref([
  { id: 'marvel', name: 'MARVEL', companyId: 420, badge: 'MARVEL', fallback: 'https://upload.wikimedia.org/wikipedia/commons/b/b9/Marvel_Logo.svg', logo_path: null, invert: false },
  { id: 'ghibli', name: 'STUDIO GHIBLI', companyId: 10342, badge: 'GHIBLI', fallback: 'https://upload.wikimedia.org/wikipedia/commons/e/e0/Studio_Ghibli_logo.svg', logo_path: null, invert: true },
  { id: 'pixar', name: 'PIXAR ANIMATION', companyId: 3, badge: 'PIXAR', fallback: 'https://upload.wikimedia.org/wikipedia/commons/4/40/Pixar_Animation_Studios_logo.svg', logo_path: null, invert: true },
  { id: 'disney', name: 'DISNEY', companyId: 2, badge: 'DISNEY', fallback: 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Disney%2B_logo.svg', logo_path: null, invert: true },
  { id: 'hbo', name: 'HBO ORIGINALS', companyId: 3268, networkId: 49, badge: 'HBO', fallback: 'https://upload.wikimedia.org/wikipedia/commons/d/de/HBO_logo.svg', logo_path: null, invert: true },
  { id: 'netflix', name: 'NETFLIX', companyId: 178464, networkId: 213, badge: 'NETFLIX', fallback: 'https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg', logo_path: null, invert: false },
  { id: 'appletv', name: 'APPLE TV+', companyId: 140087, networkId: 2552, badge: 'APPLE TV+', fallback: 'https://upload.wikimedia.org/wikipedia/commons/2/28/Apple_TV_Plus_Logo.svg', logo_path: null, invert: true },
  { id: 'dc', name: 'DC UNIVERSE', companyId: 9993, badge: 'DC', fallback: 'https://upload.wikimedia.org/wikipedia/commons/1/1c/DC_Comics_logo.svg', logo_path: null, invert: true },
  { id: 'warner', name: 'WARNER BROS', companyId: 174, badge: 'WARNER BROS', fallback: 'https://upload.wikimedia.org/wikipedia/commons/6/64/Warner_Bros_logo.svg', logo_path: null, invert: false },
  { id: 'a24', name: 'A24 FILMS', companyId: 41077, badge: 'A24', fallback: 'https://upload.wikimedia.org/wikipedia/commons/8/87/A24_logo.svg', logo_path: null, invert: true },
  { id: 'sony', name: 'SONY PICTURES', companyId: 34, badge: 'SONY', fallback: 'https://upload.wikimedia.org/wikipedia/commons/c/ca/Sony_logo.svg', logo_path: null, invert: true },
  { id: 'dreamworks', name: 'DREAMWORKS', companyId: 521, badge: 'DREAMWORKS', fallback: 'https://upload.wikimedia.org/wikipedia/commons/a/aa/DreamWorks_Animation_logo.svg', logo_path: null, invert: true },
  { id: 'starwars', name: 'LUCASFILM', companyId: 1, badge: 'LUCASFILM', fallback: 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Lucasfilm_logo.svg', logo_path: null, invert: true },
  { id: 'universal', name: 'UNIVERSAL', companyId: 33, badge: 'UNIVERSAL', fallback: 'https://upload.wikimedia.org/wikipedia/commons/c/c5/Universal_Pictures_logo.svg', logo_path: null, invert: true },
  { id: 'paramount', name: 'PARAMOUNT', companyId: 4, badge: 'PARAMOUNT', fallback: 'https://upload.wikimedia.org/wikipedia/commons/1/1a/Paramount_Pictures_logo.svg', logo_path: null, invert: true },
  { id: 'mgm', name: 'MGM', companyId: 21, badge: 'MGM', fallback: 'https://upload.wikimedia.org/wikipedia/commons/6/62/Metro-Goldwyn-Mayer_logo.svg', logo_path: null, invert: false },
  { id: 'lionsgate', name: 'LIONSGATE', companyId: 1632, badge: 'LIONSGATE', fallback: 'https://upload.wikimedia.org/wikipedia/commons/e/e7/Lionsgate_2013_logo.svg', logo_path: null, invert: true },
  { id: 'amazon', name: 'AMAZON STUDIOS', companyId: 20580, networkId: 1024, badge: 'AMAZON', fallback: 'https://upload.wikimedia.org/wikipedia/commons/1/11/Amazon_Prime_Video_logo.svg', logo_path: null, invert: false },
  { id: 'hulu', name: 'HULU', companyId: 74641, networkId: 453, badge: 'HULU', fallback: 'https://upload.wikimedia.org/wikipedia/commons/e/e4/Hulu_Logo.svg', logo_path: null, invert: false },
  { id: 'toei', name: 'TOEI ANIMATION', companyId: 5542, badge: 'TOEI ANIME', fallback: 'https://upload.wikimedia.org/wikipedia/commons/d/d4/Toei_Animation_logo.svg', logo_path: null, invert: true },
  { id: 'nickelodeon', name: 'NICKELODEON', companyId: 2348, networkId: 13, badge: 'NICKELODEON', fallback: 'https://upload.wikimedia.org/wikipedia/commons/7/7a/Nickelodeon_2023_logo.svg', logo_path: null, invert: false },
  { id: 'cartoonnetwork', name: 'CARTOON NETWORK', companyId: 546, networkId: 56, badge: 'CARTOON NETWORK', fallback: 'https://upload.wikimedia.org/wikipedia/commons/8/80/Cartoon_Network_2010_logo.svg', logo_path: null, invert: true },
  { id: 'illumination', name: 'ILLUMINATION', companyId: 3341, badge: 'ILLUMINATION', fallback: 'https://upload.wikimedia.org/wikipedia/commons/4/44/Illumination_Entertainment_logo.svg', logo_path: null, invert: true },
  { id: 'bbc', name: 'BBC STUDIOS', companyId: 3324, networkId: 4, badge: 'BBC', fallback: 'https://upload.wikimedia.org/wikipedia/commons/e/eb/BBC_logo_2021.svg', logo_path: null, invert: true },
  { id: 'pierrot', name: 'STUDIO PIERROT', companyId: 3234, badge: 'PIERROT', fallback: 'https://upload.wikimedia.org/wikipedia/commons/0/07/Studio_Pierrot_logo.svg', logo_path: null, invert: true }
]);

const fetchStudioLogos = async () => {
  try {
    const promises = studiosList.value.map(st => {
      const endpoint = st.networkId ? `${BASE_URL}/network/${st.networkId}?api_key=${API_KEY}` : `${BASE_URL}/company/${st.companyId}?api_key=${API_KEY}`;
      return axios.get(endpoint).catch(() => null);
    });
    const responses = await Promise.all(promises);
    responses.forEach((res, index) => {
      if (res?.data?.logo_path) {
        studiosList.value[index].logo_path = res.data.logo_path;
      }
    });
  } catch (err) {
    console.error("Failed to fetch TMDB studio logos", err);
  }
};

const openStudioCollection = async (studio) => {
  selectedStudio.value = studio;
  studioMovies.value = [];
  isFetchingStudio.value = true;
  try {
    const filterQuery = studio.networkId ? `with_networks=${studio.networkId}` : `with_companies=${studio.companyId}`;
    const [movieRes, tvRes] = await Promise.all([
      axios.get(`${BASE_URL}/discover/movie?api_key=${API_KEY}&${filterQuery}&sort_by=popularity.desc`).catch(() => ({ data: { results: [] } })),
      axios.get(`${BASE_URL}/discover/tv?api_key=${API_KEY}&${filterQuery}&sort_by=popularity.desc`).catch(() => ({ data: { results: [] } }))
    ]);
    const movies = (movieRes.data?.results || []).map(m => ({ ...m, media_type: 'movie' }));
    const tvs = (tvRes.data?.results || []).map(m => ({ ...m, media_type: 'tv' }));
    const combined = [...movies, ...tvs].sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
    studioMovies.value = await enrichMoviesWithLogos(combined);
  } catch (error) {
    console.error("Failed to fetch studio movies", error);
  } finally {
    isFetchingStudio.value = false;
  }
};

const isSearchOpen = ref(false);
const searchQuery = ref('');
const searchResults = ref([]);
const isSearching = ref(false);
let searchTimeout = null;

// --- SEARCH FILTER & PAGINATION STATE ---
const selectedYear = ref('');
const selectedGenres = ref([]);
const selectedType = ref(''); // Baru: Filter Movie/TV
const searchGenres = ref([]);

const toggleSearchGenre = (genreId) => {
  const idx = selectedGenres.value.indexOf(genreId);
  if (idx > -1) {
    selectedGenres.value.splice(idx, 1);
  } else {
    selectedGenres.value.push(genreId);
  }
};

const searchPage = ref(1); // Baru: Pagination
const isSearchingMore = ref(false); // Baru: Loading infinite scroll
const hasMoreSearchResults = ref(true); // Baru: Cek kalau udah nyampe akhir

const isLoggedIn = ref(false);
const currentUser = ref({ username: '' });
const isLoginOpen = ref(false);
const isProfileOpen = ref(false);
const loginData = ref({ username: '', password: '' });
const showPassword = ref(false);
const isLoggingIn = ref(false);
const loginError = ref('');

// --- LIQUID GLASS MODE STATE (full | edge | off) ---
const glassMode = ref(localStorage.getItem('viora_glass_mode') || 'edge');

const setGlassMode = (mode) => {
  glassMode.value = mode;
  localStorage.setItem('viora_glass_mode', mode);
};

const cycleGlassMode = () => {
  if (glassMode.value === 'full') setGlassMode('edge');
  else if (glassMode.value === 'edge') setGlassMode('off');
  else setGlassMode('full');
};

const isPlayerOpen = ref(false);
const currentMedia = ref(null); 
const embedUrl = ref('');

const currentPlayState = ref(null);
const isSettingsOpen = ref(false);

const isEpisodesSidebarOpen = ref(false);
const currentSeasonEpisodes = ref([]);
const tvSeasons = ref([]);
const isFetchingEpisodes = ref(false);
const isSeasonDropdownOpen = ref(false);

const selectSeason = async (seasonNumber) => {
  isSeasonDropdownOpen.value = false;
  if (currentPlayState.value.season === seasonNumber) return;
  currentPlayState.value.season = seasonNumber;
  currentPlayState.value.episode = 1;
  currentPlayState.value.startTime = 0;
  embedUrl.value = buildEmbedUrl(currentPlayState.value);
  await fetchEpisodes(currentPlayState.value.tmdbId, seasonNumber);
};

const isPlayerControlsVisible = ref(true);
const isPlayerPaused = ref(false);
let playerControlsTimer = null;

const resetPlayerControlsTimer = () => {
  isPlayerControlsVisible.value = true;
  if (playerControlsTimer) clearTimeout(playerControlsTimer);
  playerControlsTimer = setTimeout(() => {
    if (!isEpisodesSidebarOpen.value && !isPlayerPaused.value) {
      isPlayerControlsVisible.value = false;
    }
  }, 3000);
};

const playerContainerRef = ref(null);
const isFullscreen = ref(false);

const toggleFullscreen = () => {
  if (!playerContainerRef.value) return;
  if (!document.fullscreenElement && !document.webkitFullscreenElement) {
    if (playerContainerRef.value.requestFullscreen) {
      playerContainerRef.value.requestFullscreen();
    } else if (playerContainerRef.value.webkitRequestFullscreen) {
      playerContainerRef.value.webkitRequestFullscreen();
    }
    isFullscreen.value = true;
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    }
    isFullscreen.value = false;
  }
};

const handleFullscreenChange = () => {
  isFullscreen.value = !!(document.fullscreenElement || document.webkitFullscreenElement);
};

const watchHistoryMovies = ref([]); 
const watchlistMovies = ref([]); 
const isWatchlistOpen = ref(false); 
const watchlist = ref(new Set()); 

const isInfoOpen = ref(false);
const selectedMovieInfo = ref(null);
const similarMovies = ref([]);
const isFetchingInfo = ref(false);

const currentView = ref('home'); 
const browseItems = ref([]);
const isBrowseLoading = ref(false);
const isFetchingMore = ref(false);
const browsePage = ref(1);

const movieHeroMoviesList = ref([]);
const movieCategoriesList = ref([]);
const tvHeroMoviesList = ref([]);
const tvCategoriesList = ref([]);

const genresList = ref([]);
const filters = ref({
  genre: '',
  country: '',
  year: '',
  sortBy: 'popularity.desc'
});

const availableCountries = [
  { code: 'US', name: '🇺🇸 United States' },
  { code: 'KR', name: '🇰🇷 South Korea' },
  { code: 'JP', name: '🇯🇵 Japan' },
  { code: 'ID', name: '🇮🇩 Indonesia' },
  { code: 'GB', name: '🇬🇧 United Kingdom' },
  { code: 'CN', name: '🇨🇳 China' },
  { code: 'HK', name: '🇭🇰 Hong Kong' },
  { code: 'TH', name: '🇹🇭 Thailand' },
  { code: 'FR', name: '🇫🇷 France' },
  { code: 'DE', name: '🇩🇪 Germany' },
  { code: 'IN', name: '🇮🇳 India' },
  { code: 'ES', name: '🇪🇸 Spain' },
];

const availableYears = computed(() => {
  const yrs = [];
  for (let i = 2026; i >= 1977; i--) yrs.push(i);
  return yrs;
});

const activeHeroMovies = computed(() => {
  if (currentView.value === 'movie') return movieHeroMoviesList.value;
  if (currentView.value === 'tv') return tvHeroMoviesList.value;
  return heroMovies.value;
});

const activeCategories = computed(() => {
  if (currentView.value === 'movie') return movieCategoriesList.value;
  if (currentView.value === 'tv') return tvCategoriesList.value;
  return movieCategories.value;
});

// --- FILTERED RESULTS COMPUTED PROPERTY ---
const filteredResults = computed(() => {
  return searchResults.value.filter(item => {
    const yearMatch = selectedYear.value
      ? (item.release_date || item.first_air_date)?.startsWith(selectedYear.value.toString())
      : true;

    const genreMatch = selectedGenres.value.length > 0
      ? selectedGenres.value.some(gId => item.genre_ids?.includes(Number(gId)))
      : true;
      
    // Filter tipe (Movie / TV)
    const typeMatch = selectedType.value
      ? item.media_type === selectedType.value
      : true;

    return yearMatch && genreMatch && typeMatch;
  });
});

const activeModalTab = ref('history'); 
const modalFilter = ref('all'); 

const setModalTab = (tab) => {
  activeModalTab.value = tab;
  modalFilter.value = 'all'; 
};

const setModalFilter = (type) => {
  modalFilter.value = type;
  activeModalTab.value = 'history'; 
};

const filteredWatchHistoryMovies = computed(() => {
  if (modalFilter.value === 'all') return watchHistoryMovies.value;
  return watchHistoryMovies.value.filter(m => m.media_type === modalFilter.value);
});

const filteredWatchlistMovies = computed(() => {
  return watchlistMovies.value; 
});

const API_KEY = import.meta.env.VITE_TMDB_API_KEY;
const WYZIE_API_KEY = import.meta.env.VITE_WYZIE_API_KEY; 
const BASE_URL = 'https://api.themoviedb.org/3';

const getImageUrl = (path, width = 'w500') => {
  if (!path) return 'https://via.placeholder.com/300x450?text=No+Image';
  const tmdbUrl = `https://image.tmdb.org/t/p/${width}${path}`;
  
  if (width === 'original' || width === 'w780') {
    return `https://wsrv.nl/?url=${encodeURIComponent(tmdbUrl)}&output=webp&q=80&n=-1`;
  }
  
  return `https://wsrv.nl/?url=${encodeURIComponent(tmdbUrl)}&output=webp&q=60&w=300&n=-1`;
};

const logoCache = new Map();

const fetchLogo = async (id, type = 'movie') => {
  const key = `${type}_${id}`;
  if (logoCache.has(key)) return logoCache.get(key);
  try {
    const res = await axios.get(`${BASE_URL}/${type}/${id}/images?api_key=${API_KEY}&include_image_language=en,null`);
    const logo = res.data.logos?.find(l => l.file_path.endsWith('.png')) || res.data.logos?.[0];
    const path = logo ? logo.file_path : null;
    logoCache.set(key, path);
    return path;
  } catch (e) {
    logoCache.set(key, null);
    return null;
  }
};

const enrichMoviesWithLogos = async (movies) => {
  return Promise.all(movies.map(async (m) => {
    const movieId = m.tmdb_id || m.id;
    const logoPath = await fetchLogo(movieId, m.media_type || 'movie');
    return { ...m, id: movieId, logo_path: logoPath };
  }));
};

const fetchUserData = async () => {
  if (!isLoggedIn.value) return;
  try {
    const historyRes = await api.get('/api/watch-history/');
    const historyData = historyRes.data;
    if (Array.isArray(historyData) && historyData.length > 0) {
      const historyDetails = await Promise.all(
        historyData.map(async (item) => {
          let mediaType = item.media_type || 'movie';
          try {
            // Attempt 1: Fetch with primary saved media type
            const tmdbRes = await axios.get(`${BASE_URL}/${mediaType}/${item.tmdb_id}?api_key=${API_KEY}`);
            return { 
              ...tmdbRes.data, 
              id: item.tmdb_id,
              media_type: mediaType, 
              progress_percentage: item.progress_percentage,
              season: item.season, 
              episode: item.episode,
              current_time_seconds: item.current_time_seconds,
              total_duration: item.total_duration
            };
          } catch(e) {
            // Attempt 2: Fallback try opposite media type (e.g. if movie failed 404, try tv)
            const altType = mediaType === 'movie' ? 'tv' : 'movie';
            try {
              const altRes = await axios.get(`${BASE_URL}/${altType}/${item.tmdb_id}?api_key=${API_KEY}`);
              return {
                ...altRes.data,
                id: item.tmdb_id,
                media_type: altType,
                progress_percentage: item.progress_percentage,
                season: item.season,
                episode: item.episode,
                current_time_seconds: item.current_time_seconds,
                total_duration: item.total_duration
              };
            } catch(e2) {
              // Attempt 3: If TMDB returns 404 for both, use basic info saved in database item
              if (item.title || item.name || item.poster_path) {
                return {
                  id: item.tmdb_id,
                  title: item.title || item.name,
                  name: item.title || item.name,
                  poster_path: item.poster_path,
                  backdrop_path: item.backdrop_path,
                  vote_average: item.rating || 0,
                  release_date: item.year ? `${item.year}-01-01` : '',
                  media_type: mediaType,
                  progress_percentage: item.progress_percentage,
                  season: item.season,
                  episode: item.episode,
                  current_time_seconds: item.current_time_seconds,
                  total_duration: item.total_duration
                };
              }
              return null;
            }
          }
        })
      );
      const validHistory = historyDetails.filter(Boolean);
      watchHistoryMovies.value = validHistory;
      
      // Non-blocking background logo enrichment
      enrichMoviesWithLogos(validHistory).then(enriched => {
        watchHistoryMovies.value = enriched;
      }).catch(() => {});
    } else {
      watchHistoryMovies.value = [];
    }
  } catch (error) { 
    watchHistoryMovies.value = [];
  }
};

const handleRemoveHistory = async (movie) => {
  try {
    await api.delete('/api/watch-history/', { data: { tmdb_id: movie.id, media_type: movie.media_type }});
    watchHistoryMovies.value = watchHistoryMovies.value.filter(m => m.id !== movie.id);
  } catch (err) { console.error("❌ Failed remove history", err); }
};

const fetchAllData = async () => {
  try {
    const [trending, topRatedMovies, action, animation, topRatedTv, korean, horror, family, kidsTv, animeTv, upcoming] = await Promise.all([
      axios.get(`${BASE_URL}/trending/all/day?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/movie/top_rated?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/discover/movie?api_key=${API_KEY}&with_genres=28`),
      axios.get(`${BASE_URL}/discover/movie?api_key=${API_KEY}&with_genres=16`),
      axios.get(`${BASE_URL}/tv/top_rated?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/discover/tv?api_key=${API_KEY}&with_origin_country=KR`),
      axios.get(`${BASE_URL}/discover/movie?api_key=${API_KEY}&with_genres=27`),
      axios.get(`${BASE_URL}/discover/movie?api_key=${API_KEY}&with_genres=10751`), 
      axios.get(`${BASE_URL}/discover/tv?api_key=${API_KEY}&with_genres=10762`), 
      axios.get(`${BASE_URL}/discover/tv?api_key=${API_KEY}&with_genres=16&with_original_language=ja`),
      axios.get(`${BASE_URL}/movie/upcoming?api_key=${API_KEY}`)
    ]);

    const validTrending = trending.data.results.filter(m => m.vote_average > 0);
    heroMovies.value = await enrichMoviesWithLogos(validTrending.slice(0, 8));
    
    if (upcoming.data?.results) {
      const validUpcoming = upcoming.data.results.filter(m => m.poster_path || m.backdrop_path).map(m => ({ ...m, media_type: 'movie' }));
      upcomingMovies.value = validUpcoming.slice(0, 10);
    }
    
    const categoriesData = [
      { id: 1, title: 'Trending Now', layout: 'landscape', raw: validTrending.slice(5, 15) },
      { id: 2, title: 'Top Rated TV Series', layout: 'hero-card', raw: topRatedTv.data.results.slice(0, 10).map(m=>({...m, media_type: 'tv'})) },
      { id: 3, title: 'K-Dramas', layout: 'portrait', raw: korean.data.results.slice(0, 10).map(m=>({...m, media_type: 'tv'})) },
      { id: 4, title: 'Horror Fests', layout: 'hero-card', raw: horror.data.results.slice(0, 10).map(m=>({...m, media_type: 'movie'})) },
      { id: 5, title: 'Top Rated Movies', layout: 'landscape', raw: topRatedMovies.data.results.slice(0, 10).map(m=>({...m, media_type: 'movie'})) },
      { id: 6, title: 'Action Thriller', layout: 'portrait', raw: action.data.results.slice(0, 10).map(m=>({...m, media_type: 'movie'})) },
      { id: 7, title: 'Animation Series', layout: 'landscape', raw: animation.data.results.slice(0, 10).map(m=>({...m, media_type: 'movie'})) },
    ];
    
    fetchStudioLogos();

    movieCategories.value = await Promise.all(categoriesData.map(async (cat) => ({
      id: cat.id, title: cat.title, layout: cat.layout, movies: await enrichMoviesWithLogos(cat.raw)
    })));

    const kidsCatsData = [
      { id: 'k1', title: 'Top Animation', layout: 'portrait', raw: animation.data.results.slice(10, 20).map(m=>({...m, media_type: 'movie'})) },
      { id: 'k2', title: 'Family Movies', layout: 'landscape', raw: family.data.results.slice(0, 10).map(m=>({...m, media_type: 'movie'})) },
      { id: 'k3', title: 'Kids TV Shows', layout: 'portrait', raw: kidsTv.data.results.slice(0, 10).map(m=>({...m, media_type: 'tv'})) },
      { id: 'k4', title: 'Anime Universe', layout: 'landscape', raw: animeTv.data.results.slice(0, 10).map(m=>({...m, media_type: 'tv'})) },
    ];
    
    kidsCategories.value = await Promise.all(kidsCatsData.map(async (cat) => ({
      id: cat.id, title: cat.title, layout: cat.layout, movies: await enrichMoviesWithLogos(cat.raw)
    })));
    
    startHeroCarousel();
    isLoading.value = false;
  } catch (error) { console.error(error); } finally { isLoading.value = false; }
};

const fetchMoviePageData = async () => {
  if (movieCategoriesList.value.length > 0) return; 
  try {
    const [nowPlaying, popular, topRated, upcoming] = await Promise.all([
      axios.get(`${BASE_URL}/movie/now_playing?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/movie/popular?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/movie/top_rated?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/movie/upcoming?api_key=${API_KEY}`)
    ]);

    const popData = popular.data.results
      .filter(m => m.vote_average > 0)
      .map(m => ({...m, media_type: 'movie'}));
    movieHeroMoviesList.value = await enrichMoviesWithLogos(popData.slice(0, 8));

    const cats = [
      { id: 'm1', title: 'Now Playing', layout: 'hero-card', raw: nowPlaying.data.results.slice(0, 10).map(m => ({...m, media_type: 'movie'})) },
      { id: 'm2', title: 'Popular Movies', layout: 'portrait', raw: popData.slice(8, 20) },
      { id: 'm3', title: 'Top Rated', layout: 'landscape', raw: topRated.data.results.slice(0, 10).map(m => ({...m, media_type: 'movie'})) },
      { id: 'm4', title: 'Upcoming', layout: 'portrait', raw: upcoming.data.results.slice(0, 10).map(m => ({...m, media_type: 'movie'})) }
    ];
    movieCategoriesList.value = await Promise.all(cats.map(async (cat) => ({ id: cat.id, title: cat.title, layout: cat.layout, movies: await enrichMoviesWithLogos(cat.raw) })));
  } catch(e) { console.error(e); }
};

const fetchTvPageData = async () => {
  if (tvCategoriesList.value.length > 0) return; 
  try {
    const [airingToday, onTheAir, popular, topRated] = await Promise.all([
      axios.get(`${BASE_URL}/tv/airing_today?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/tv/on_the_air?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/tv/popular?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/tv/top_rated?api_key=${API_KEY}`)
    ]);

    const popData = popular.data.results
      .filter(m => m.vote_average > 0)
      .map(m => ({...m, media_type: 'tv'}));
    tvHeroMoviesList.value = await enrichMoviesWithLogos(popData.slice(0, 8));

    const cats = [
      { id: 't1', title: 'Airing Today', layout: 'hero-card', raw: airingToday.data.results.slice(0, 10).map(m => ({...m, media_type: 'tv'})) },
      { id: 't2', title: 'On The Air', layout: 'portrait', raw: onTheAir.data.results.slice(0, 10).map(m => ({...m, media_type: 'tv'})) },
      { id: 't3', title: 'Popular Series', layout: 'landscape', raw: popData.slice(8, 20) },
      { id: 't4', title: 'Top Rated', layout: 'portrait', raw: topRated.data.results.slice(0, 10).map(m => ({...m, media_type: 'tv'})) }
    ];
    tvCategoriesList.value = await Promise.all(cats.map(async (cat) => ({ id: cat.id, title: cat.title, layout: cat.layout, movies: await enrichMoviesWithLogos(cat.raw) })));
  } catch(e) { console.error(e); }
};

const fetchGenres = async () => {
  try {
    const type = currentView.value === 'tv' ? 'tv' : 'movie';
    const res = await axios.get(`${BASE_URL}/genre/${type}/list?api_key=${API_KEY}`);
    genresList.value = res.data.genres;
  } catch(e) { console.error(e); }
};

const fetchSearchGenres = async () => {
  try {
    const [movieRes, tvRes] = await Promise.all([
      axios.get(`${BASE_URL}/genre/movie/list?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/genre/tv/list?api_key=${API_KEY}`)
    ]);
    
    const combined = [...movieRes.data.genres, ...tvRes.data.genres];
    const uniqueGenres = Array.from(new Set(combined.map(a => a.id)))
      .map(id => combined.find(a => a.id === id));
      
    searchGenres.value = uniqueGenres;
  } catch (error) {
    console.error("Failed to load search genres", error);
  }
};

const applyFilters = async () => {
  isBrowseLoading.value = true;
  browseItems.value = [];
  browsePage.value = 1;
  await loadMoreBrowseItems();
  isBrowseLoading.value = false;
};

const changeView = async (viewType) => {
  if (currentView.value === viewType) return; 
  
  if (lenis) {
    lenis.scrollTo(0, { immediate: false }); 
  } else {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  currentView.value = viewType;
  
  if(heroTimer) clearInterval(heroTimer);
  
  if (viewType === 'home') {
    currentHeroIndex.value = 0;
    startHeroCarousel();
    return;
  }
  
  filters.value = { genre: '', country: '', year: '', sortBy: 'popularity.desc' };
  isBrowseLoading.value = true;
  browseItems.value = [];
  browsePage.value = 1;

  if (viewType === 'movie') await fetchMoviePageData();
  if (viewType === 'tv') await fetchTvPageData();

  currentHeroIndex.value = 0;
  startHeroCarousel();
  
  await fetchGenres();
  await applyFilters();
  isBrowseLoading.value = false;
};
const handleImageLoad = (e) => {
  e.target.style.opacity = '1';
  e.target.style.transform = 'scale(1)'; 

  const skeleton = e.target.previousElementSibling;
  if (skeleton && skeleton.classList.contains('skeleton-overlay')) {
    skeleton.style.opacity = '0';
    setTimeout(() => skeleton.remove(), 500); 
  }
};

const smoothHorizontalScroll = (e) => {
  const isHorizontalScroll = Math.abs(e.deltaX) > 0 || (e.shiftKey && Math.abs(e.deltaY) > 0);

  if (isHorizontalScroll) {
    e.preventDefault(); 
    
    const scrollAmount = e.deltaX !== 0 ? e.deltaX : e.deltaY;
    
    e.currentTarget.scrollBy({
      left: scrollAmount * 4, 
      behavior: 'smooth'
    });
  }
};

const loadMoreBrowseItems = async () => {
  if (!isLoggedIn.value && browsePage.value > 1) return;
  if (isFetchingMore.value) return;
  isFetchingMore.value = true;
  
  try {
    const type = currentView.value === 'tv' ? 'tv' : 'movie';
    const yearParam = type === 'movie' ? 'primary_release_year' : 'first_air_date_year';

    let endpoint = `${BASE_URL}/discover/${type}?api_key=${API_KEY}&page=${browsePage.value}&sort_by=${filters.value.sortBy}`;
    if (filters.value.genre) endpoint += `&with_genres=${filters.value.genre}`;
    if (filters.value.year) endpoint += `&${yearParam}=${filters.value.year}`;
    if (filters.value.country) endpoint += `&with_origin_country=${filters.value.country}`;

    const res = await axios.get(endpoint);
    
    const rawItems = res.data.results.slice(0, 15);
    const enrichedItems = await enrichMoviesWithLogos(rawItems.map(item => ({...item, media_type: currentView.value})));
    
    browseItems.value = [...browseItems.value, ...enrichedItems];
    browsePage.value++;
  } catch (error) {
    console.error("Failed to load more items", error);
  } finally {
    isFetchingMore.value = false;
  }
};

const openInfo = async (movie) => {
  isInfoOpen.value = true;
  isFetchingInfo.value = true;
  selectedMovieInfo.value = movie; 
  similarMovies.value = [];

  try {
    const type = movie.media_type === 'tv' ? 'tv' : 'movie';
    const [detailsRes, creditsRes, similarRes] = await Promise.all([
      axios.get(`${BASE_URL}/${type}/${movie.id}?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/${type}/${movie.id}/credits?api_key=${API_KEY}`),
      axios.get(`${BASE_URL}/${type}/${movie.id}/similar?api_key=${API_KEY}`)
    ]);

    selectedMovieInfo.value = {
      ...movie,
      ...detailsRes.data,
      cast: creditsRes.data.cast.slice(0, 6),
      production_companies: detailsRes.data.production_companies || [] 
    };

    const rawSimilar = similarRes.data.results.slice(0, 12).map(s => ({...s, media_type: type}));
    similarMovies.value = await enrichMoviesWithLogos(rawSimilar);

  } catch (err) {
    console.error("Failed to fetch info details", err);
  } finally {
    isFetchingInfo.value = false;
  }
};

const closeInfo = () => {
  isInfoOpen.value = false;
  setTimeout(() => {
    selectedMovieInfo.value = null;
    similarMovies.value = [];
  }, 300); 
};

const toggleSearch = async () => {
  if (isLoginOpen.value) isLoginOpen.value = false;
  if (isProfileOpen.value) isProfileOpen.value = false;
  if (isWatchlistOpen.value) isWatchlistOpen.value = false;
  
  isSearchOpen.value = !isSearchOpen.value;
  
  if (isSearchOpen.value) {
    await fetchSearchGenres(); 
    nextTick(() => document.getElementById('viora-search-input')?.focus());
  }
};

const toggleWatchlist = () => {
  if (!isLoggedIn.value) { isLoginOpen.value = true; return; }
  if (isSearchOpen.value) isSearchOpen.value = false;
  if (isProfileOpen.value) isProfileOpen.value = false;
  
  // ⚡ INSTANT 0ms MODAL TOGGLE
  isWatchlistOpen.value = !isWatchlistOpen.value;

  if (isWatchlistOpen.value) {
    // Non-blocking background fetch
    fetchUserData();
    fetchWatchlist();
  }
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
  const movieId = movie.id || movie.tmdb_id;
  try {
    const res = await api.post('/api/watchlist/toggle/', {
      tmdb_id: movieId, media_type: mediaType, title: movie.title || movie.name,
      poster_path: movie.poster_path, backdrop_path: movie.backdrop_path,
      rating: movie.vote_average, year: (movie.release_date || movie.first_air_date)?.substring(0, 4)
    });
    if (res.data.status === "added") { watchlist.value.add(movieId); } 
    else { watchlist.value.delete(movieId); }
    await fetchWatchlist();
  } catch (err) { console.error("❌ Failed to update watchlist", err); }
};

// --- LOGIC SEARCH INITIAL FETCH (Page 1) ---
const performSearch = async () => {
  if (!searchQuery.value.trim()) { 
    searchResults.value = []; 
    hasMoreSearchResults.value = false;
    return; 
  }
  
  isSearching.value = true;
  searchPage.value = 1;
  hasMoreSearchResults.value = true;
  
  try {
    const res = await axios.get(`${BASE_URL}/search/multi?api_key=${API_KEY}&query=${encodeURIComponent(searchQuery.value)}&include_adult=false&page=1`);
    // Filter out person/other types
    const rawResults = res.data.results.filter(item => item.media_type === 'movie' || item.media_type === 'tv');
    searchResults.value = await enrichMoviesWithLogos(rawResults);
    
    if (res.data.page >= res.data.total_pages) {
      hasMoreSearchResults.value = false;
    }
  } catch (error) { 
    console.error(error); 
  } finally { 
    isSearching.value = false; 
  }
};

// --- LOGIC SEARCH INFINITE SCROLL (Page > 1) ---
const loadMoreSearchResults = async () => {
  if (isSearchingMore.value || !hasMoreSearchResults.value || !searchQuery.value.trim()) return;
  
  isSearchingMore.value = true;
  searchPage.value++;
  
  try {
    const res = await axios.get(`${BASE_URL}/search/multi?api_key=${API_KEY}&query=${encodeURIComponent(searchQuery.value)}&include_adult=false&page=${searchPage.value}`);
    const rawResults = res.data.results.filter(item => item.media_type === 'movie' || item.media_type === 'tv');
    const newEnriched = await enrichMoviesWithLogos(rawResults);
    
    searchResults.value = [...searchResults.value, ...newEnriched];
    
    if (res.data.page >= res.data.total_pages) {
      hasMoreSearchResults.value = false;
    }
  } catch (error) {
    console.error(error);
  } finally {
    isSearchingMore.value = false;
  }
};

// --- DETECT SCROLL IN SEARCH MODAL ---
const handleSearchScroll = (e) => {
  const { scrollTop, scrollHeight, clientHeight } = e.target;
  // Trigger fetch if scrolled near bottom (50px threshold)
  if (scrollTop + clientHeight >= scrollHeight - 50) {
    loadMoreSearchResults();
  }
};

const onSearchInput = () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(performSearch, 500);
};

const fetchWatchlist = async () => {
  if (!isLoggedIn.value) return; 
  try {
    const res = await api.get('/api/watchlist/');
    const items = Array.isArray(res.data) ? res.data : [];
    watchlist.value = new Set(items.map(item => item.id || item.tmdb_id));
    const watchListDetails = await Promise.all(
      items.map(async (item) => {
        try {
          if (item.poster_path && item.title) {
            return { ...item, id: item.id || item.tmdb_id };
          }
          const tmdbRes = await axios.get(`${BASE_URL}/${item.media_type}/${item.id || item.tmdb_id}?api_key=${API_KEY}`);
          return { ...tmdbRes.data, media_type: item.media_type };
        } catch(e) {
          return { ...item, id: item.id || item.tmdb_id };
        }
      })
    );
    watchlistMovies.value = await enrichMoviesWithLogos(watchListDetails.filter(Boolean));
  } catch (err) { 
    console.error("gagal ambil watchlist", err); 
    watchlistMovies.value = [];
  }
};

const handleLogin = async () => {
  if (!loginData.value.username || !loginData.value.password) { loginError.value = 'Please fill in all fields.'; return; }
  isLoggingIn.value = true;
  loginError.value = '';
  try {
    const response = await api.post('/api/login/', {
      username: loginData.value.username,
      password: loginData.value.password
    });
    isLoggedIn.value = true;
    currentUser.value = { username: response.data.username, email: response.data.email };
    localStorage.setItem('viora_auth_user', response.data.username);
    await fetchUserData();
    await fetchWatchlist();
    isLoginOpen.value = false;
    loginData.value = { username: '', password: '' };
  } catch (error) {
    console.error(error);
    loginError.value = error.response?.data?.detail || 'Login gagal. Cek username dan password.';
  } finally { isLoggingIn.value = false; }
};


const handleLogout = async () => {
  try { await api.post('/api/logout/'); } catch (e) {}
  isLoggedIn.value = false;
  currentUser.value = { username: '' };
  isProfileOpen.value = false;
  isWatchlistOpen.value = false;
  watchHistoryMovies.value = [];
  watchlistMovies.value = [];
  watchlist.value.clear();
  localStorage.removeItem('viora_auth_user');
  
  // Kick user out of the player and return to home instantly
  if (isPlayerOpen.value) {
    closePlayer();
  }
  currentView.value = 'home';
};


const checkLoginStatus = async () => {
  // Cek session aktif via /api/me/ — lebih reliable daripada cek localStorage
  try {
    const res = await api.get('/api/me/');
    isLoggedIn.value = true;
    currentUser.value = { username: res.data.username, email: res.data.email };
    localStorage.setItem('viora_auth_user', res.data.username);
    await fetchUserData();
    await fetchWatchlist();
  } catch (e) {
    // Tidak ada session aktif
    isLoggedIn.value = false;
    currentUser.value = { username: '' };
    localStorage.removeItem('viora_auth_user');
  }
};


const buildEmbedUrl = (playState) => {
  if (!playState) return '';
  const { tmdbId, type, season, episode, startTime } = playState;
  const progressParam = startTime ? `&progress=${startTime}` : '';
  if (type === 'movie') {
    return `https://player.videasy.net/movie/${tmdbId}?overlay=false&color=3B82F6${progressParam}`;
  } else {
    return `https://player.videasy.net/tv/${tmdbId}/${season}/${episode}?nextEpisode=true&autoplayNextEpisode=true&episodeSelector=false&overlay=false&color=3B82F6${progressParam}`;
  }
};

let deleteBtnInterval = null;
watch(isPlayerOpen, (isOpen) => {
  if (isOpen) {
    deleteBtnInterval = setInterval(() => {
      const btn = document.getElementById('ButtonFullscreen');
      if (btn) btn.remove();
    }, 300);
  } else {
    if (deleteBtnInterval) clearInterval(deleteBtnInterval);
  }
});

const fetchEpisodes = async (tmdbId, seasonNumber) => {
  isFetchingEpisodes.value = true;
  try {
    const res = await axios.get(`${BASE_URL}/tv/${tmdbId}/season/${seasonNumber}?api_key=${API_KEY}`);
    currentSeasonEpisodes.value = res.data.episodes || [];
  } catch(e) {
    console.error("Failed to fetch episodes", e);
  } finally {
    isFetchingEpisodes.value = false;
  }
};

const changeEpisode = async (seasonNumber, episodeNumber) => {
  const isNewSeason = currentPlayState.value.season !== seasonNumber;
  
  currentPlayState.value.season = seasonNumber;
  currentPlayState.value.episode = episodeNumber;
  currentPlayState.value.startTime = 0;
  
  const history = watchHistoryMovies.value.find(m => m.id === currentPlayState.value.tmdbId);
  if (history && history.season === seasonNumber && history.episode === episodeNumber) {
     currentPlayState.value.startTime = Math.floor(history.current_time_seconds || history.progress_percentage || 0);
  }

  embedUrl.value = buildEmbedUrl(currentPlayState.value);
  isEpisodesSidebarOpen.value = false;

  if (isNewSeason) {
    await fetchEpisodes(currentPlayState.value.tmdbId, seasonNumber);
  }
};

const handleSeasonChange = async (event) => {
  const newSeason = parseInt(event.target.value);
  await fetchEpisodes(currentPlayState.value.tmdbId, newSeason);
};

const openPlayer = (movie) => {
  if (!isLoggedIn.value) { isLoginOpen.value = true; return; }
  const type = movie.media_type === 'tv' ? 'tv' : 'movie'; 
  currentMedia.value = movie;
  
  let startTime = 0;
  const tmdbId = movie.showId || movie.id;
  const history = watchHistoryMovies.value.find(m => m.id === tmdbId);
  
  let targetSeason = movie.season;
  let targetEpisode = movie.episode;

  if (history) {
    if (!targetSeason) targetSeason = history.season;
    if (!targetEpisode) targetEpisode = history.episode;
    if ((!movie.season || movie.season === history.season) && (!movie.episode || movie.episode === history.episode)) {
      startTime = Math.floor(history.current_time_seconds || history.progress_percentage || 0); 
    }
  }

  targetSeason = targetSeason || 1;
  targetEpisode = targetEpisode || 1;

  currentPlayState.value = {
    tmdbId,
    type,
    season: targetSeason,
    episode: targetEpisode,
    startTime
  };

  // ⚡ INSTANT PLAYER LAUNCH (0ms DELAY)
  embedUrl.value = buildEmbedUrl(currentPlayState.value);
  isPlayerOpen.value = true;
  isPlayerPaused.value = false;
  resetPlayerControlsTimer();

  if (heroTimer) clearInterval(heroTimer); 
  if (isInfoOpen.value) closeInfo(); 
  if (selectedStudio.value) selectedStudio.value = null;

  // Async background fetch for TV episodes sidebar (does NOT block player launch)
  if (type === 'tv') {
    isEpisodesSidebarOpen.value = false;
    (async () => {
      if (movie.seasons) {
        tvSeasons.value = movie.seasons;
      } else {
        try {
          const res = await axios.get(`${BASE_URL}/tv/${tmdbId}?api_key=${API_KEY}`);
          tvSeasons.value = res.data.seasons || [];
        } catch(e) {}
      }
      fetchEpisodes(tmdbId, targetSeason);
    })();
  } else {
    isEpisodesSidebarOpen.value = false;
    currentSeasonEpisodes.value = [];
    tvSeasons.value = [];
  }
};

const closePlayer = () => {
  embedUrl.value = '';
  isEpisodesSidebarOpen.value = false;
  isPlayerPaused.value = false;
  if (playerControlsTimer) clearTimeout(playerControlsTimer);
  if (document.fullscreenElement || document.webkitFullscreenElement) {
    if (document.exitFullscreen) document.exitFullscreen().catch(() => {});
    else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
  }
  setTimeout(() => {
    isPlayerOpen.value = false;
    currentMedia.value = null;
    currentPlayState.value = null;
    startHeroCarousel(); 
    fetchUserData();
  }, 100); 
};

let lastSaveTime = 0;
const saveWatchProgress = async (playerEvent, id, mediaType, season, episode, progress, currentTime, duration) => {
  if (!isLoggedIn.value || !id) return;
  const now = Date.now();
  const normalizedEvent = String(playerEvent || '').toLowerCase();
  const isEnded = normalizedEvent === 'ended' || normalizedEvent.includes('end');
  const isPause = normalizedEvent === 'pause' || normalizedEvent.includes('pause');

  if (isPause) {
    isPlayerPaused.value = true;
  } else if (normalizedEvent.includes('play') || normalizedEvent.includes('timeupdate') || normalizedEvent.includes('progress')) {
    isPlayerPaused.value = false;
  }
  
  if (isEnded || isPause || now - lastSaveTime > 3000) {
    lastSaveTime = now; 
    try {
      await api.post('/api/watch-history/', {
        tmdb_id: Number(id),
        media_type: mediaType || 'movie',
        season: season ? Number(season) : null,
        episode: episode ? Number(episode) : null,
        progress_percentage: Math.min(100, Math.max(0, Math.round(progress || 0))),
        current_time_seconds: Math.floor(currentTime || 0),
        total_duration: Math.floor(duration || 0),
        is_finished: isEnded
      });
    } catch (e) {
      console.error('Failed to save watch progress:', e);
    }
  }
};

const handlePlayerMessage = async (event) => {
  try {
    let message = event.data;
    if (typeof message === 'string') {
      try {
        message = JSON.parse(message);
      } catch (e) {
        return;
      }
    }

    if (!message || typeof message !== 'object') return;



    // Format 2: Videasy & Standard postMessage players ({ event / type / playerState, currentTime, duration, progress, id, ... })
    const playerEvent = message.event || message.type || message.action || message.playerEvent || message.status;
    if (!playerEvent) return;

    const currentTime = message.currentTime ?? message.current_time ?? message.time ?? 0;
    const duration = message.duration ?? message.totalDuration ?? message.total_duration ?? 0;
    let progress = message.progress ?? message.percentage ?? message.progress_percentage;

    if ((progress === undefined || progress === null) && duration > 0) {
      progress = (currentTime / duration) * 100;
    }

    const id = message.id || message.tmdb_id || message.tmdbId || message.data?.id || currentPlayState.value?.tmdbId;
    const mediaType = message.mediaType || message.media_type || message.data?.mediaType || currentPlayState.value?.type;
    const season = message.season ?? message.data?.season ?? currentPlayState.value?.season;
    const episode = message.episode ?? message.data?.episode ?? currentPlayState.value?.episode;

    await saveWatchProgress(playerEvent, id, mediaType, season, episode, progress, currentTime, duration);
  } catch (e) {}
};

let ticking = false;
const handleScroll = ({ scroll }) => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      isScrolled.value = scroll > 50;
      
      // Calculate scroll progress for VIORA About Reveal section at page bottom
      const docHeight = document.body.scrollHeight || document.documentElement.scrollHeight;
      const windowHeight = window.innerHeight;
      const maxScroll = docHeight - windowHeight;
      if (maxScroll > 0) {
        const distanceToBottom = maxScroll - scroll;
        // As scroll approaches bottom 600px, progress goes from 0 (separated) to 1 (gathered together)
        if (distanceToBottom <= 600) {
          vioraProgress.value = Math.min(1, Math.max(0, 1 - (distanceToBottom / 600)));
        } else {
          vioraProgress.value = 0;
        }
      }

      ticking = false;
      if (!isLoggedIn.value && (currentView.value === 'movie' || currentView.value === 'tv')) {
        if (scroll > 1200 && !hasShownAutoLogin.value && !isLoginOpen.value) {
          isLoginOpen.value = true;
          hasShownAutoLogin.value = false; 
        }
      }
      
      if (currentView.value !== 'home' && !isBrowseLoading.value && !isFetchingMore.value) {
        const bottomOfWindow = scroll + window.innerHeight >= docHeight - 500;
        if (bottomOfWindow) {
          loadMoreBrowseItems();
        }
      }
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
    if (isInfoOpen.value) closeInfo();
  }
};

const startHeroCarousel = () => {
  if(heroTimer) clearInterval(heroTimer);
  heroTimer = setInterval(() => {
    if(activeHeroMovies.value.length > 0) {
      currentHeroIndex.value = (currentHeroIndex.value + 1) % activeHeroMovies.value.length;
    }
  }, 8000);
};

const navItems = [
  { key: 'home', action: () => changeView('home') },
  { key: 'movie', action: () => changeView('movie') },
  { key: 'tv', action: () => changeView('tv') },
  { key: 'watchlist', action: toggleWatchlist }
]

watch(currentView, (val) => {
  if (val === 'home') activeIndex.value = 0
  if (val === 'movie') activeIndex.value = 1
  if (val === 'tv') activeIndex.value = 2
})

watch(hoverIndex, () => {
  if (hoverIndex.value !== null) {
    isAnimating.value = true
    setTimeout(() => {
      isAnimating.value = false
    }, 180) 
  }
})
let lenisRafId;
// Daftar domain iklan/tracker yang sering dibuka oleh embed player pihak ketiga
const AD_TRACKER_DOMAINS = [
  'doubleclick', 'googlesyndication', 'adnxs', 'adsrvr', 'rubiconproject',
  'openx', 'smartadserver', 'pubmatic', 'criteo', 'taboola', 'outbrain',
  'revcontent', 'bidswitch', 'quantserve', 'scorecardresearch', 'moatads',
  'amazon-adsystem', 'ib.adnxs', 'pagead', 'adservice', 'clicks.trafficjunky',
  'popads', 'popcash', 'plugrush', 'exoclick', 'trafficfactory', 'ero-advertising',
  'juicyads', 'adsterraserving', 'datahc.com', 'tpc.googlesyndication', 'google-analytics.com'
];

const blockAdsAndTrackers = () => {
  const _originalOpen = window.open;
  window.open = function(url, name, specs) {
    if (!url) return null;
    try {
      const href = String(url).toLowerCase();
      // Blokir URL yang mengandung domain tracker/ads
      const isAd = AD_TRACKER_DOMAINS.some(d => href.includes(d));
      // Blokir juga popup yang tidak punya URL jelas (javascript:, about:blank tricks)
      const isSuspicious = href.startsWith('javascript:') || href === 'about:blank' || href === '';
      if (isAd || isSuspicious) {
        console.info('[Viora] Blocked popup/tracker:', url);
        return null;
      }
    } catch (e) {}
    return _originalOpen.call(window, url, name, specs);
  };
};

onMounted(() => {
  // Anti Inspect Element & Right Click
  window.addEventListener('contextmenu', (e) => e.preventDefault());
  window.addEventListener('keydown', (e) => {
    if (e.key === 'F12' || 
        (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j' || e.key === 'C' || e.key === 'c')) ||
        (e.ctrlKey && (e.key === 'U' || e.key === 'u'))) {
      e.preventDefault();
    }
  });

  if (typeof window !== 'undefined') {
    lenis = new Lenis({
        duration: 0.9,
        easing: (t) => 1 - Math.pow(1 - t, 3), // cubic ease-out: snappy start, smooth stop
        smoothWheel: true,
        wheelMultiplier: 1.2,
        touchMultiplier: 2
    })

    function raf(time) {
        lenis.raf(time)
        lenisRafId = requestAnimationFrame(raf) 
    }
    lenisRafId = requestAnimationFrame(raf)
    lenis.on('scroll', handleScroll) // Use Lenis scroll event — avoids double-firing with window scroll
    window.addEventListener('mousemove', handleMouseMove)
  }
  
  blockAdsAndTrackers();
  checkLoginStatus();
  fetchAllData();
  startHeroCardAutoScroll();
  window.addEventListener('keydown', handleKeydown);
  window.addEventListener('message', handlePlayerMessage); 
});

onUnmounted(() => {
  if (lenisRafId) cancelAnimationFrame(lenisRafId); 
  if (lenis) lenis.destroy();
  window.removeEventListener('mousemove', handleMouseMove)
  window.removeEventListener('keydown', handleKeydown);
  window.removeEventListener('message', handlePlayerMessage);
  if (heroTimer) clearInterval(heroTimer);
  if (heroCardAutoScrollTimer) clearInterval(heroCardAutoScrollTimer);
});
</script>

<template>
  
  <div :class="['min-h-screen bg-[radial-gradient(circle_at_20%_30%,rgba(59,130,246,0.08),transparent_40%)] text-white font-sans selection:bg-blue-500/30 overflow-x-hidden pb-32', `glass-mode-${glassMode}`]">
    
    <Transition
      enter-active-class="transition-opacity duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div data-lenis-prevent v-if="isInfoOpen" class="fixed inset-0 z-[150] bg-black/0 overflow-y-auto flex justify-center items-start pt-10 pb-10 hide-scrollbar" @click.self="closeInfo">
        <div class="w-full max-w-4xl rounded-2xl shadow-2xl overflow-hidden relative border border-white/10" @click.stop style="background: #18181be6;">
          <button @click="closeInfo" class="absolute top-4 right-4 z-50 p-2 bg-black/60 hover:bg-white/20 rounded-full text-white transition-colors">
            <X class="w-6 h-6" />
          </button>
          

          <div class="relative w-full aspect-video md:aspect-[21/9] bg-black">
            <img loading="lazy" decoding="async" v-if="selectedMovieInfo?.backdrop_path || selectedMovieInfo?.poster_path" :src="getImageUrl(selectedMovieInfo.backdrop_path || selectedMovieInfo.poster_path, selectedMovieInfo.backdrop_path ? 'original' : 'w500')" :class="selectedMovieInfo.backdrop_path ? 'object-cover' : 'object-contain'" class="w-full h-full opacity-80" />
            <div class="absolute inset-0 bg-gradient-to-t from-[#18181b] via-[#18181b]/30 to-transparent"></div>

            <div class="absolute bottom-8 left-8 right-8">
              <img loading="lazy" decoding="async" v-if="selectedMovieInfo?.logo_path" :src="getImageUrl(selectedMovieInfo.logo_path, 'w500')" class="max-w-[250px] md:max-w-[400px] max-h-[100px] object-contain drop-shadow-2xl mb-6 origin-left" />
              <h2 v-else class="text-4xl md:text-5xl font-black  uppercase tracking-tighter drop-shadow-2xl mb-4 text-white">
                {{ selectedMovieInfo?.title || selectedMovieInfo?.name }}
              </h2>
              
              <div class="flex gap-3">
                <Button @click="openPlayer(selectedMovieInfo)" class="bg-white text-black hover:bg-blue-500 hover:text-white font-bold px-8 h-12 rounded-xl transition-colors">
                  <Play class="w-5 h-5 mr-2 fill-current" /> Play
                </Button>
                <Button @click="handleWatchlistToggle(selectedMovieInfo)" variant="outline" class="bg-black/40  border-white/20 hover:bg-white/10 h-12 px-8 rounded-xl font-bold transition-colors">
                  <Check v-if="watchlist.has(selectedMovieInfo?.id)" class="w-5 h-5 mr-2 text-green-400" />
                  <Bookmark v-else class="w-5 h-5 mr-2" />
                  My List
                </Button>
              </div>
            </div>
          </div>

          <div class="p-8 grid grid-cols-1 md:grid-cols-3 gap-8">
            <div class="md:col-span-2 space-y-4">
              <div class="flex flex-wrap items-center gap-3 text-sm font-bold text-gray-400">
                <span class="text-green-500">{{ (selectedMovieInfo?.vote_average * 10)?.toFixed(0) }}% Match</span>
                <span>{{ (selectedMovieInfo?.release_date || selectedMovieInfo?.first_air_date)?.substring(0,4) }}</span>
                <span v-if="selectedMovieInfo?.runtime" class="border border-gray-600 px-1.5 py-0.5 rounded">{{ selectedMovieInfo.runtime }} min</span>
                <span class="border border-gray-600 px-1.5 py-0.5 rounded text-white">
                  {{
                    selectedMovieInfo?.media_type === 'tv' 
                      ? 'Series' 
                      : selectedMovieInfo?.media_type === 'movie' 
                        ? 'Movie' 
                        : 'Unknown'
                  }}
                </span>
                <span class="border border-gray-600 px-1.5 py-0.5 rounded text-white font-medium">FHD</span>
                <span class="border border-gray-600 px-1.5 py-0.5 rounded text-white">CC</span>
              </div>
              <p class="text-[15px] md:text-base leading-relaxed text-gray-200">{{ selectedMovieInfo?.overview || 'No overview available.' }}</p>
            </div>

            <div class="space-y-6 text-sm">
                <div v-if="selectedMovieInfo?.genres?.length">
                  <span class="text-white font-bold block mb-1">Genres</span>
                  <div class="flex flex-wrap gap-2 mt-1">
                    <span v-for="g in selectedMovieInfo.genres" :key="g.id" class="bg-white/10 text-gray-300 px-2.5 py-1 rounded text-xs font-medium">{{ g.name }}</span>
                  </div>
                </div>

                <div class="flex gap-3 mt-2">
                  <div class="flex items-center gap-1 bg-white/10 border border-white/20 rounded-xl px-3 py-1">
                    <Star class="w-4 h-4 text-yellow-400" />
                    <span class="text-gray-300 text-xs font-medium">{{ selectedMovieInfo.vote_average }}/10</span>
                  </div>
                  <div class="flex items-center gap-1 bg-white/10 border border-white/20 rounded-xl px-3 py-1">
                    <Flame class="w-4 h-4 text-red-400" />
                    <span class="text-gray-300 text-xs font-medium">{{ selectedMovieInfo.popularity?.toFixed(1) }}</span>
                  </div>
                </div>
              </div>
          </div>

          <div class="p-8 pt-0">
              <div class="space-y-12 text-sm">
                  <div v-if="selectedMovieInfo.seasons?.length" class="mt-6">
                    <h3 class="text-lg font-bold mb-3 flex items-center gap-2"><span class="w-1.5 h-6 bg-blue-500 rounded-full"></span> Seasons</h3>
                    <div class="flex gap-4 overflow-x-auto pb-2">
                      <div v-for="season in selectedMovieInfo.seasons.map(s => ({ ...s, media_type: 'tv', season: s.season_number ?? 1, episode: 1, showId:selectedMovieInfo.id}))" :key="season.id" class="flex-shrink-0 w-32 cursor-pointer hover:scale-105 transition-transform duration-300" @click="openPlayer(season)">
                        <div class="relative aspect-[2/3] rounded-lg overflow-hidden shadow-lg">
                          <img loading="lazy" decoding="async" :src="getImageUrl(season.poster_path, 'w300')" class="w-full h-full object-cover" :alt="season.name" />
                          <div class="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs p-1 text-center">{{ season.episode_count }} eps</div>
                        </div>
                        <h3 class="text-xs font-semibold mt-1 line-clamp-2 text-white"> {{ season.season_number }}</h3>
                        <h4 class="text-xs font-semibold mt-1 line-clamp-2 text-white">{{ season.name }}</h4>
                        <div class="text-[10px] text-green-400 mt-0.5 font-bold">{{ season.vote_average ? season.vote_average.toFixed(1) : '-' }}</div>
                      </div>
                    </div>
                  </div>
              </div>
            </div>

       <div class="p-8 pt-0">
          <div class="space-y-12 text-sm">
            <div v-if="selectedMovieInfo?.cast?.length" class="space-y-12">
              <h4 class="text-white font-bold mb-2">Cast</h4>
              <div class="flex gap-4 overflow-x-auto py-2">
                <div v-for="actor in selectedMovieInfo.cast" :key="actor.id" class="flex items-center gap-3 w-45 flex-shrink-0 cursor-pointer transform transition-transform transition-shadow hover:scale-105 hover:shadow-lg bg-white/10  border border-white/20 rounded-2xl p-1">
                  <div class="w-16 h-16 rounded-full overflow-hidden bg-gray-800 flex-shrink-0">
                    <img loading="lazy" decoding="async" :src="getImageUrl(actor.profile_path, 'w185')" :alt="actor.name" class="w-full h-full object-cover" />
                  </div>
                  <div class="flex-1">
                    <span class="text-gray-300 text-sm font-medium leading-snug break-words">{{ actor.name }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="p-8 pt-0">
          <div class="space-y-12 text-sm">
            <div v-if="selectedMovieInfo?.production_companies?.length">
              <h4 class="text-white font-bold mb-2">Production Companies</h4>
              <div class="flex gap-4 overflow-x-auto py-2">
                <template v-for="company in selectedMovieInfo.production_companies" :key="company.id || company.name">
                  <div v-if="company.logo_path" class="flex items-center gap-3 w-45 flex-shrink-0 cursor-pointer transform transition-transform transition-shadow hover:scale-105 hover:shadow-lg bg-white border border-white/20 rounded-2xl p-5">
                    <div >
                      <img loading="lazy" decoding="async" :src="`https://image.tmdb.org/t/p/w185${company.logo_path}`" :alt="company.name" />
                    </div>
                  </div>
                </template>
              </div>
            </div>
            <div v-else class="bg-white/10 border border-white/20 rounded-xl p-4 flex justify-center items-center">
              <p>No company logo available</p>
            </div>
          </div>
        </div>
          
          <div class="p-8 pt-0" v-if="similarMovies.length">
            <h3 class="text-xl font-bold mb-4 flex items-center gap-2"><span class="w-1.5 h-6 bg-blue-500 rounded-full"></span> More Like This</h3>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div v-for="sim in similarMovies" :key="sim.id" class="bg-[#2b2b30]/50 rounded-xl overflow-hidden cursor-pointer hover:scale-105 transition-transform duration-300 shadow-lg" @click="openInfo(sim)">
                <div class="relative aspect-video">
                  <img loading="lazy" decoding="async" :src="getImageUrl(sim.backdrop_path, 'w500')" class="w-full h-full object-cover opacity-80" />
                  <div class="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-100 bg-black/40 transition-opacity">
                    <Play class="w-10 h-10 text-white fill-current drop-shadow-lg" @click.stop="openPlayer(sim)" />
                  </div>
                  <div class="absolute top-2 right-2 text-xs font-bold px-1.5 py-0.5 bg-black/60 rounded text-white">
                     {{ sim.media_type === 'tv' ? 'Series' : 'Movie' }}
                  </div>
                </div>
                <div class="p-3">
                  <div class="flex justify-between items-start mb-1">
                    <img loading="lazy" decoding="async" v-if="sim.logo_path" :src="getImageUrl(sim.logo_path, 'w300')" class="max-h-[30px] max-w-[120px] object-contain drop-shadow-md origin-left flex-1" />
                    <h4 v-else class="font-bold text-sm line-clamp-1 flex-1 text-white">{{ sim.title || sim.name }}</h4>
                    
                    <button @click.stop="handleWatchlistToggle(sim)" class="ml-2 border border-white/30 rounded-full p-1 hover:bg-white/10 transition">
                      <Check v-if="watchlist.has(sim.id)" class="w-3 h-3 text-green-400" />
                      <Plus v-else class="w-3 h-3 text-white" />
                    </button>
                  </div>
                  <div class="text-[10px] text-gray-400 font-bold mt-1">
                    <span class="text-green-500 mr-2">{{ (sim.vote_average * 10).toFixed(0) }}% Match</span>
                    {{ (sim.release_date || sim.first_air_date)?.substring(0,4) }}
                  </div>
                  <p class="text-xs text-gray-500 line-clamp-3 mt-2">{{ sim.overview }}</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isPlayerOpen" ref="playerContainerRef" @mousemove="resetPlayerControlsTimer" class="fixed inset-0 z-[200] bg-black flex flex-col items-center justify-center">
        <!-- Top Hover Trigger Zone: Invisible overlay over iframe top area (limited to left side to avoid blocking sidebar) -->
        <div 
          @mousemove="resetPlayerControlsTimer"
          @mouseenter="resetPlayerControlsTimer"
          class="!fixed top-0 left-0 right-0 sm:right-[420px] h-28 z-[390] pointer-events-auto"
        ></div>

        <!-- Top Controls: Close Player, Episodes Toggle, Fullscreen Toggle -->
        <div 
          @mouseenter="resetPlayerControlsTimer"
          class="!fixed top-4 left-4 md:top-6 md:left-6 z-[400] flex items-center gap-3 transition-opacity duration-500"
          :class="isPlayerControlsVisible || isEpisodesSidebarOpen || isPlayerPaused ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'"
        >
          <button 
            @click.stop="closePlayer" 
            class="p-2.5 md:p-3 bg-black/60 hover:bg-red-600 rounded-full transition-all duration-300 text-white shadow-2xl cursor-pointer border border-white/20 hover:scale-105"
            title="Tutup Player"
          >
            <X class="w-6 h-6 md:w-7 md:h-7" />
          </button>

          <button 
            v-if="currentPlayState?.type === 'tv'"
            @click.stop="isEpisodesSidebarOpen = !isEpisodesSidebarOpen" 
            class="px-4 py-2.5 md:py-3 bg-black/60 hover:bg-blue-600 rounded-full transition-all duration-300 text-white shadow-2xl cursor-pointer border border-white/20 flex items-center gap-2 font-bold text-sm hover:scale-105"
            title="Daftar Episode"
          >
            <Menu class="w-5 h-5" />
            <span class="hidden sm:inline">Episodes</span>
          </button>

          <button 
            @click.stop="toggleFullscreen" 
            class="p-2.5 md:p-3 bg-black/60 hover:bg-blue-600 rounded-full transition-all duration-300 text-white shadow-2xl cursor-pointer border border-white/20 hover:scale-105"
            :title="isFullscreen ? 'Kecilkan Layar' : 'Layar Penuh'"
          >
            <Minimize v-if="isFullscreen" class="w-5 h-5 md:w-6 md:h-6" />
            <Maximize v-else class="w-5 h-5 md:w-6 md:h-6" />
          </button>
        </div>

        <!-- Top Right: Logo / Title -->
        <div 
          class="!fixed top-4 right-6 md:top-6 md:right-8 z-[350] text-right hidden sm:block transition-opacity duration-500"
          :class="isPlayerControlsVisible || isEpisodesSidebarOpen || isPlayerPaused ? 'opacity-100' : 'opacity-0'"
        >
          <img loading="lazy" decoding="async" 
            v-if="currentMedia?.logo_path" 
            :src="getImageUrl(currentMedia.logo_path, 'w300')" 
            class="max-h-[35px] md:max-h-[45px] max-w-[200px] md:max-w-[300px] object-contain drop-shadow-lg" 
            :alt="currentMedia?.title || currentMedia?.name" 
          />
          <h2 
            v-else 
            class="text-xl md:text-2xl font-black uppercase tracking-tighter drop-shadow-md text-white"
          >
            {{ currentMedia?.title || currentMedia?.name }}
          </h2>
        </div>

       <div v-if="embedUrl" class="w-full h-full relative overflow-hidden">
           <div class="w-full h-full">
             <iframe 
               :src="embedUrl" 
               width="100%" 
               height="100%" 
               frameborder="0" 
               allowfullscreen 
               allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; screen-orientation; fullscreen"
               class="w-full h-full"
             ></iframe>
           </div>
           <!-- Invisible overlay to close sidebar when clicking outside -->
           <div 
             v-if="isEpisodesSidebarOpen" 
             class="!fixed inset-0 z-[490] pointer-events-auto" 
             @click.stop="isEpisodesSidebarOpen = false"
           ></div>

           <!-- Episodes Sidebar Drawer -->
           <div 
             v-if="currentPlayState?.type === 'tv'"
             class="!fixed top-0 right-0 bottom-0 w-full sm:w-[380px] md:w-[420px] bg-[#09090b]/85 border-l border-white/15 z-[500] flex flex-col transition-transform duration-300 ease-in-out shadow-[-20px_0_60px_rgba(0,0,0,0.9)] pointer-events-auto"
             :class="isEpisodesSidebarOpen ? 'translate-x-0' : 'translate-x-full'"
           >
             <!-- Sidebar Header -->
             <div class="p-4 md:p-5 border-b border-white/15 flex justify-between items-center bg-[#121215] pt-6 md:pt-5">
               <h3 class="font-black text-white text-base tracking-wider uppercase flex items-center gap-2">
                 <span class="w-1.5 h-6 bg-blue-500 rounded-full"></span>
                 Episodes List
               </h3>
              
             </div>

             <!-- Season Selector Dropdown (Custom UI) -->
             <div class="p-3.5 border-b border-white/10 relative z-50 pointer-events-auto" v-if="tvSeasons.length > 0">
               <button 
                 @click.stop="isSeasonDropdownOpen = !isSeasonDropdownOpen"
                 class="w-full bg-[#18181b] hover:bg-[#27272a] border border-white/10 rounded-xl text-white px-4 py-2.5 flex items-center justify-between font-bold text-xs transition-all shadow-md cursor-pointer group"
               >
                 <div class="flex items-center gap-2">
                   <Layers class="w-4 h-4 text-blue-400" />
                   <span>Season {{ currentPlayState.season }}</span>
                 </div>
                 <ChevronDown class="w-4 h-4 text-white/70 transition-transform duration-300 group-hover:text-white" :class="isSeasonDropdownOpen ? 'rotate-180' : ''" />
               </button>

               <!-- Dropdown Menu Options -->
               <Transition name="fade">
                 <div 
                   v-if="isSeasonDropdownOpen" 
                   class="absolute left-3.5 right-3.5 top-full mt-2 bg-[#121215] border border-white/20 rounded-xl shadow-2xl overflow-hidden z-[100] max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 pointer-events-auto"
                 >
                   <div 
                     v-for="season in tvSeasons.filter(s => s.season_number > 0)" 
                     :key="season.id"
                     @click.stop="selectSeason(season.season_number)"
                     class="px-4 py-2.5 text-xs font-semibold text-white/80 hover:text-white hover:bg-blue-600/30 cursor-pointer flex justify-between items-center transition-colors border-b border-white/5 last:border-0"
                     :class="currentPlayState.season === season.season_number ? 'bg-blue-600/25 text-blue-400 font-bold' : ''"
                   >
                     <span>Season {{ season.season_number }}</span>
                     <span class="text-[10px] text-white/40 font-normal" v-if="season.episode_count">{{ season.episode_count }} Episodes</span>
                   </div>
                 </div>
               </Transition>
             </div>

             <!-- Episodes List Container -->
             <div data-lenis-prevent class="flex-1 overflow-y-auto p-3 flex flex-col gap-3 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent overscroll-contain pb-10">
               <div v-if="isFetchingEpisodes" class="flex justify-center p-10">
                 <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
               </div>
               <div v-else-if="currentSeasonEpisodes.length === 0" class="p-4 text-center text-white/50 text-xs font-medium">
                 No episodes found.
               </div>
               <div 
                 v-else
                 v-for="ep in currentSeasonEpisodes" 
                 :key="ep.id"
                 @click="changeEpisode(currentPlayState.season, ep.episode_number)"
                 class="flex gap-3.5 p-3 rounded-xl cursor-pointer transition-all duration-200 group items-center relative bg-white/5 border border-white/10 hover:bg-white/15 hover:border-white/20 shadow-sm"
                 :class="currentPlayState.episode === ep.episode_number ? '!bg-blue-600/30 !border-blue-500 ring-1 ring-blue-500/80 shadow-[0_0_20px_rgba(59,130,246,0.3)]' : ''"
               >
                 <!-- Thumbnail -->
                 <div class="w-28 h-16 bg-black/80 rounded-lg overflow-hidden relative flex-shrink-0 shadow-md border border-white/10">
                   <img loading="lazy" decoding="async" v-if="ep.still_path" :src="getImageUrl(ep.still_path, 'w300')" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 opacity-90" />
                   <div class="absolute inset-0 flex items-center justify-center bg-black/40 group-hover:bg-black/20 transition-colors">
                     <Play class="w-6 h-6 text-white drop-shadow-md" :class="currentPlayState.episode === ep.episode_number ? 'text-blue-400 fill-current' : ''" />
                   </div>
                 </div>

                 <!-- Details -->
                 <div class="flex-1 min-w-0 pr-1">
                   <div class="flex items-center justify-between gap-1 mb-0.5">
                     <h4 class="text-white text-xs font-bold truncate transition-colors" :class="currentPlayState.episode === ep.episode_number ? 'text-blue-300 font-extrabold' : 'group-hover:text-blue-300'">
                       {{ ep.episode_number }}. {{ ep.name }}
                     </h4>
                     <span v-if="currentPlayState.episode === ep.episode_number" class="text-[9px] bg-blue-500 text-white font-black px-1.5 py-0.5 rounded-md uppercase tracking-wider flex-shrink-0">Playing</span>
                   </div>
                   <p class="text-white/60 text-[11px] line-clamp-2 leading-snug font-medium">{{ ep.overview || 'No description available.' }}</p>
                 </div>
               </div>
             </div>
           </div>
       </div>
      </div>
    </Transition>

    <Transition name="vision-pro">
      <div data-lenis-prevent v-if="isWatchlistOpen" class="fixed inset-0 z-[50] flex items-center justify-center p-4 md:p-10 bg-black/0 transition-all duration-300" @click.self="toggleWatchlist">
        
        <!-- Replaced mix-blend-screen+blur orbs (GPU killer) with CSS gradient — same look, zero GPU cost -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none" style="background: radial-gradient(circle at 25% 25%, rgba(59,130,246,0.12) 0%, transparent 60%), radial-gradient(circle at 75% 75%, rgba(168,85,247,0.10) 0%, transparent 60%);"></div>

        <aside class="!fixed right-4 md:right-10 top-1/2 -translate-y-1/2 z-50 hidden lg:flex flex-col liquidGlass-wrapper shadow-[0_20px_50px_-10px_rgba(0,0,0,0.5)] !rounded-full w-16">
          <div class="liquidGlass-effect !rounded-full"></div>
          <div class="liquidGlass-tint !rounded-full"></div>
          <div class="liquidGlass-shine !rounded-full"></div>
          <div class="liquidGlass-text flex flex-col gap-6 px-3 py-6 items-center w-full relative z-10">
            
            <div @click="setModalFilter('all')" class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 relative group" :class="activeModalTab === 'history' && modalFilter === 'all' ? 'bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.4)] scale-110' : 'hover:bg-white/10 text-white/60 hover:text-white'">
              <PlayCircle class="w-5 h-5 transition-transform group-hover:scale-110" />
              <div class="absolute right-14 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">All History</div>
            </div>
            
            <div class="w-8 h-[1px] bg-white/10 rounded-full"></div>
            
            <div @click="setModalFilter('movie')" class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 relative group" :class="activeModalTab === 'history' && modalFilter === 'movie' ? 'bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.4)] scale-110' : 'hover:bg-white/10 text-white/60 hover:text-white'">
              <Film class="w-5 h-5 transition-transform group-hover:scale-110" />
              <div class="absolute right-14 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">Movies History</div>
            </div>
            
            <div @click="setModalFilter('tv')" class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 relative group" :class="activeModalTab === 'history' && modalFilter === 'tv' ? 'bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.4)] scale-110' : 'hover:bg-white/10 text-white/60 hover:text-white'">
              <Tv class="w-5 h-5 transition-transform group-hover:scale-110" />
              <div class="absolute right-14 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">TV Shows History</div>
            </div>

            <div class="w-8 h-[1px] bg-white/10 rounded-full"></div>

            <div @click="setModalTab('watchlist')" class="w-10 h-10 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 relative group" :class="activeModalTab === 'watchlist' ? 'bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.4)] scale-110' : 'hover:bg-white/10 text-white/60 hover:text-white'">
              <Bookmark class="w-5 h-5 transition-transform group-hover:scale-110" />
              <div class="absolute right-14 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">Saved Items</div>
            </div>

          </div>
        </aside>

        <div class="liquidGlass-wrapper shadow-[0_25px_80px_-20px_rgba(0,0,0,1)] !rounded-[3rem] relative w-full max-w-6xl h-[80vh] flex flex-col z-10" @click.stop>
          <div class="liquidGlass-effect !rounded-[3rem]"></div>
          <div class="liquidGlass-tint !rounded-[3rem]"></div>
          <div class="liquidGlass-shine !rounded-[3rem]"></div>
          <div class="liquidGlass-text relative w-full h-full flex flex-col z-10 overflow-hidden">
            
            <div class="px-8 py-4 md:px-7 md:py-4 flex justify-between items-center border-b border-white/10 bg-white/5 z-20 rounded-t-[3rem]">
              <div class="flex items-center gap-5">
                  <div class="p-3.5 bg-white/10 rounded-3xl shadow-[inset_0_1px_1px_rgba(255,255,255,0.4)] border border-white/20">
                    <Play v-if="activeModalTab === 'history'" class="w-4 h-4 text-white fill-white/20" />
                    <Bookmark v-else class="w-4 h-4 text-white fill-white/20" />
                  </div>
                  <div>
                    <h5 class="text-xl md:text-3xl font-bold tracking-tight text-white">
                      {{ activeModalTab === 'history' ? 'My Watch History' : 'Saved Items' }}
                    </h5>
                  </div>
              </div>
              
              <button @click="toggleWatchlist" class="p-3.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.3)] transition-all hover:scale-105 active:scale-95">
                <X class="w-4 h-4 text-white/90" />
              </button>
            </div>

            <div data-lenis-prevent class="flex-1 overflow-y-auto hide-scrollbar p-8 md:p-12 relative z-10 pb-32">
              
              <template v-if="activeModalTab === 'history'">
                <div v-if="watchHistoryMovies.length === 0" class="h-full flex flex-col items-center justify-center">
                  <div class="w-24 h-24 mb-6 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                    <PlayCircle class="w-8 h-8 text-white/40" />
                  </div>
                  <h3 class="text-2xl font-bold mb-2 text-white">No Watch History</h3>
                  <p class="text-white/50 mb-8">You haven't watched anything yet.</p>
                </div>

                <div v-else-if="filteredWatchHistoryMovies.length === 0" class="h-full flex flex-col items-center justify-center">
                  <h3 class="text-xl font-bold text-white/50">No {{ modalFilter === 'movie' ? 'Movies' : 'TV Series' }} in your history.</h3>
                </div>

               <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div v-for="movie in filteredWatchHistoryMovies" :key="movie.id" @click="openPlayer(movie)" class="relative flex-none rounded-3xl overflow-hidden bg-black/40 transition-transform duration-500 hover:scale-105 hover:z-40 transform-gpu group cursor-pointer border border-white/10 aspect-video col-span-1 shadow-2xl">
                    
                    <div class="skeleton-overlay absolute inset-0 bg-white/5 animate-pulse z-0"></div>
                    
                    <img loading="lazy" decoding="async" :src="movie.backdrop_path || movie.poster_path ? getImageUrl(movie.backdrop_path || movie.poster_path, 'w780') : 'https://via.placeholder.com/780x438?text=No+Image'" 
                         class="relative z-10 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
                         style="opacity: 0; transform: scale(1.05);" 
                         @load="handleImageLoad" />
                    
                    <div class="absolute bottom-0 left-0 w-full h-1.5 bg-black/80 z-30">
                      <div class="h-full bg-blue-500 rounded-r-full shadow-[0_0_10px_rgba(59,130,246,0.8)]" :style="{ width: (movie.progress_percentage || 0) + '%' }"></div>
                    </div>

                    <div class="absolute z-20 inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent p-5 flex flex-col justify-end items-start pointer-events-none">
                      <img loading="lazy" decoding="async" v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w300')" class="max-w-[140px] max-h-[45px] object-contain drop-shadow-lg mb-1 origin-bottom-left" />
                      <h4 v-else class="text-sm font-black uppercase tracking-tighter line-clamp-1 drop-shadow-md text-white mb-1">{{ movie.title || movie.name }}</h4>
                    </div>

                    <div class="absolute top-3 right-3 z-30 flex items-center gap-2">
                      <button @click.stop="openInfo(movie)" class="p-2 bg-black/40 hover:bg-white hover:text-black rounded-full transition-colors border border-white/20">
                        <Info class="w-4 h-4 text-inherit" />
                      </button>
                      <button @click.stop="handleWatchlistToggle(movie, movie.media_type)" class="p-2 bg-black/40 hover:bg-yellow-400 rounded-full transition-colors border border-white/20 hover:border-yellow-400">
                        <Check v-if="watchlist.has(movie.id)" class="w-4 h-4 text-blue-900 font-black" />
                        <Bookmark v-else class="w-4 h-4 text-white hover:text-blue-900" />
                      </button>
                      <button @click.stop="handleRemoveHistory(movie)" class="p-2 bg-black/40 hover:bg-red-600 rounded-full transition-colors border border-white/20 hover:border-red-500">
                        <X class="w-4 h-4 text-white" />
                      </button>
                    </div>

                    <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                       <div class="w-14 h-14 bg-white/25 rounded-full flex items-center justify-center border border-white/40 transform scale-50 group-hover:scale-100 transition-transform shadow-xl">
                          <Play class="w-6 h-6 text-white fill-current" />
                       </div>
                    </div>

                  </div>
                </div>
              </template>

              <template v-else>
                <div v-if="filteredWatchlistMovies.length === 0" class="h-full flex flex-col items-center justify-center">
                  <div class="w-24 h-24 mb-6 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                    <Bookmark class="w-8 h-8 text-white/40" />
                  </div>
                  <h3 class="text-2xl font-bold mb-2 text-white">Your Saved List is Empty</h3>
                  <p class="text-white/50 mb-8">Save movies and series to watch them later.</p>
                </div>

                <div v-else class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
                  <div v-for="movie in filteredWatchlistMovies" :key="movie.id" @click="openPlayer(movie)" class="relative flex-none rounded-3xl overflow-hidden bg-black/40 transition-transform duration-500 hover:scale-105 hover:z-40 transform-gpu group cursor-pointer border border-white/10 aspect-[2/3] col-span-1 shadow-2xl">
                    <div class="skeleton-overlay absolute inset-0 bg-white/5 animate-pulse z-0"></div>
                    <img loading="lazy" decoding="async" :src="movie.poster_path || movie.backdrop_path ? getImageUrl(movie.poster_path || movie.backdrop_path, 'w500') : 'https://via.placeholder.com/500x750?text=No+Image'" class="relative z-10 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" style="opacity: 0; transform: scale(1.05);" @load="handleImageLoad" />
                    
                    <div class="absolute z-20 inset-0 bg-gradient-to-t from-black/90 via-black/10 to-transparent p-4 flex flex-col justify-end items-center pointer-events-none">
                      <img loading="lazy" decoding="async" v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w300')" class="max-w-[120px] max-h-[40px] object-contain drop-shadow-lg" />
                      <h4 v-else class="text-sm font-black uppercase tracking-tighter line-clamp-2 drop-shadow-md text-center text-white">{{ movie.title || movie.name }}</h4>
                    </div>
                    
                    <div class="absolute top-3 right-3 z-30 flex items-center gap-2">
                     <button @click.stop="openInfo(movie)" class="p-2 bg-black/40 hover:bg-white hover:text-black rounded-full transition-colors border border-white/20">
                      <Info class="w-4 h-4 text-inherit" />
                    </button>
                      <button @click.stop="handleWatchlistToggle(movie)" class="p-2 bg-black/40 hover:bg-red-500 rounded-full transition-colors border border-white/20">
                        <Check v-if="watchlist.has(movie.id)" class="w-4 h-4 text-white font-black" />
                        <Bookmark v-else class="w-4 h-4 text-white" />
                      </button>
                    </div>
                  </div>
                </div>
              </template>

            </div>
          </div>
        </div>
      </div>
    </Transition>

   <Transition name="fade">
      <div 
        data-lenis-prevent
        v-if="isSearchOpen"
        class="fixed inset-0 z-[100] bg-black/0 flex justify-center items-start pt-[12vh]"
        @click.self="toggleSearch"
      >

        <div class="relative w-full max-w-5xl mx-4 flex gap-4">

          <!-- Main Search Panel with Liquid Glass -->
          <div class="liquidGlass-wrapper flex-1 !rounded-3xl shadow-[0_25px_80px_-20px_rgba(0,0,0,1)] relative overflow-hidden">
            <div class="liquidGlass-effect !rounded-3xl"></div>
            <div class="liquidGlass-tint !rounded-3xl"></div>
            <div class="liquidGlass-shine !rounded-3xl"></div>
            <div class="liquidGlass-text w-full relative z-10">

              <div class="flex items-center px-6 py-5 border-b border-white/10 bg-white/5">
                <Search class="w-6 h-6 text-white mr-4" />

                <input
                  id="viora-search-input"
                  v-model="searchQuery"
                  @input="onSearchInput"
                  placeholder="Search movies, series, or actors..."
                  class="flex-1 bg-transparent outline-none text-xl text-white placeholder:text-white/80 font-medium
                  focus:drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]"
                  autocomplete="off"
                />

                <button 
                  v-if="searchQuery"
                  @click="searchQuery = ''; searchResults = []"
                  class="p-1 mr-2 hover:bg-white/10 rounded-full transition"
                >
                  <X class="w-5 h-5 text-gray-400" />
                </button>

                <div class="px-2 py-1 bg-white/10 rounded text-[10px] font-bold text-gray-400 tracking-widest uppercase hidden md:block">
                  ESC
                </div>
              </div>

              <div v-if="searchQuery" class="max-h-[65vh] overflow-y-auto hide-scrollbar p-3" @scroll="handleSearchScroll">

                <div v-if="isSearching" class="py-24 flex flex-col items-center justify-center gap-6">
                  <div class="relative w-20 h-20 flex items-center justify-center">
                    <div class="absolute inset-0 border-4 border-blue-500/20 rounded-full"></div>
                    <div class="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <Search class="w-8 h-8 text-white animate-pulse" />
                  </div>
                  <div class="text-center">
                    <h3 class="text-xl font-bold text-white mb-1">Searching Universe...</h3>
                    <p class="text-sm text-gray-400">Looking for "<span class="text-white">{{ searchQuery }}</span>"</p>
                  </div>
                </div>

                <div v-else-if="filteredResults.length === 0" class="py-24 flex flex-col items-center justify-center gap-5">
                  <div class="relative w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mb-2 shadow-inner border border-white/10">
                    <Search class="w-10 h-10 text-white opacity-80" />
                    <div class="absolute top-2 right-2 w-7 h-7 bg-red-500 rounded-full flex items-center justify-center border-2 border-[#18181b]">
                      <X class="w-4 h-4 text-white font-bold" />
                    </div>
                  </div>
                  <div class="text-center">
                    <h3 class="text-2xl font-black text-white mb-2 tracking-tight">No matches found</h3>
                    <p class="text-gray-400 max-w-sm mx-auto leading-relaxed">
                      We couldn't find anything for "<span class="text-white font-medium">{{ searchQuery }}</span>". Try adjusting your keywords or browse our categories.
                    </p>
                  </div>
                </div>

                <!-- Rich Watch-History Style Card Grid for Search Results -->
                <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 p-2">
                  <div 
                    v-for="item in filteredResults"
                    :key="item.id"
                    @click="openPlayer(item)"
                    class="relative flex-none rounded-2xl overflow-hidden bg-[#18181b] transition-transform duration-500 hover:scale-105 hover:z-40 transform-gpu group cursor-pointer border border-white/10 aspect-video col-span-1 shadow-xl ring-1 ring-white/5"
                  >
                    <!-- Skeleton Overlay -->
                    <div class="skeleton-overlay absolute inset-0 bg-[#27272a]/60 animate-pulse z-0"></div>

                    <!-- Backdrop / Poster Image -->
                    <img 
                      :src="item.backdrop_path || item.poster_path ? getImageUrl(item.backdrop_path || item.poster_path, 'w780') : 'https://via.placeholder.com/780x438?text=No+Image'"
                      loading="lazy"
                      decoding="async"
                      class="relative z-10 w-full h-full object-cover opacity-85 group-hover:opacity-100 transition-transform transition-opacity duration-700 group-hover:scale-105" 
                      style="opacity: 0; transform: scale(1.02);" 
                      @load="handleImageLoad" 
                      :alt="item.title || item.name"
                    />

                    <!-- Content Overlay -->
                    <div class="absolute z-20 inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent p-4 flex flex-col justify-end items-start pointer-events-none">
                      <!-- Title or Logo -->
                      <img loading="lazy" decoding="async" 
                        v-if="item.logo_path" 
                        :src="getImageUrl(item.logo_path, 'w300')" 
                        class="max-w-[130px] max-h-[38px] object-contain drop-shadow-md mb-1.5 origin-bottom-left" 
                      />
                      <h4 
                        v-else 
                        class="text-sm font-black uppercase tracking-tighter line-clamp-1 drop-shadow-md text-white mb-1"
                      >
                        {{ item.title || item.name }}
                      </h4>

                      <!-- Badges (Type, Year, Rating Badges) -->
                      <div class="flex items-center gap-1.5 text-[11px] font-bold text-gray-300 flex-wrap">
                        <span class="bg-blue-500/20 border border-blue-500/40 text-blue-400 px-2 py-0.5 rounded-md uppercase tracking-wider text-[10px] font-black">
                          {{ item.media_type === 'tv' ? 'Series' : 'Movie' }}
                        </span>
                        <span v-if="item.release_date || item.first_air_date" class="px-2 py-0.5 bg-black/60 border border-white/20 text-white/90 rounded-md text-[10px] font-bold shadow-sm">
                          {{ (item.release_date || item.first_air_date)?.substring(0,4) }}
                        </span>
                        <span v-if="item.vote_average" class="px-2 py-0.5 bg-yellow-400/20 border border-yellow-400/40 text-yellow-300 rounded-md text-[10px] font-bold shadow-sm">
                          {{ item.vote_average?.toFixed(1) }}
                        </span>
                      </div>
                    </div>

                    <!-- Top Action Buttons (Info & Watchlist) -->
                    <div class="absolute top-3 right-3 z-30 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <button 
                        @click.stop="openInfo(item)" 
                        class="p-2 bg-black/60 hover:bg-white hover:text-black rounded-full transition-colors border border-white/20 text-white"
                        title="Info"
                      >
                        <Info class="w-3.5 h-3.5" />
                      </button>
                      <button 
                        @click.stop="handleWatchlistToggle(item, item.media_type)" 
                        class="p-2 bg-black/60 hover:bg-yellow-400 hover:text-blue-950 text-white rounded-full transition-colors border border-white/20"
                        title="Bookmark"
                      >
                        <Check v-if="watchlist.has(item.id)" class="w-3.5 h-3.5 text-green-400 font-bold" />
                        <Bookmark v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>

                    <!-- Hover Center Play Button (Ultra-lightweight, zero blur) -->
                    <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none z-30">
                      <div class="w-12 h-12 bg-black/70 text-white rounded-full flex items-center justify-center border border-white/30 transform scale-75 group-hover:scale-100 transition-transform shadow-xl">
                        <Lock v-if="!isLoggedIn" class="w-5 h-5 text-white" />
                        <Play v-else class="w-5 h-5 fill-current ml-0.5" />
                      </div>
                    </div>

                  </div>
                </div>
                  
                  <div v-if="isSearchingMore" class="p-4 flex justify-center">
                    <Loader2 class="w-6 h-6 animate-spin text-blue-500" />
                  </div>
                </div>
              </div>
            </div>

          <!-- Search Filter Sidebar with Liquid Glass -->
          <div class="liquidGlass-wrapper w-[220px] hidden md:flex flex-col !rounded-3xl relative overflow-hidden">
            <div class="liquidGlass-effect !rounded-3xl"></div>
            <div class="liquidGlass-tint !rounded-3xl"></div>
            <div class="liquidGlass-shine !rounded-3xl"></div>
            <div class="liquidGlass-text w-full p-4 relative z-10 flex flex-col gap-4">

              <h3 class="text-white text-sm font-semibold opacity-80">Filter</h3>
              
              <div>
                <p class="text-xs text-gray-400 mb-2">Type</p>
                <select v-model="selectedType"
                  class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
                  <option value="">All</option>
                  <option value="movie">Movies</option>
                  <option value="tv">TV Series</option>
                </select>
              </div>

              <div>
                <p class="text-xs text-gray-400 mb-2">Year</p>
                <select v-model="selectedYear"
                  class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white">
                  <option value="">All</option>
                  <option v-for="year in availableYears" :key="year" :value="year">
                    {{ year }}
                  </option>
                </select>
              </div>

              <div>
                <div class="flex justify-between items-center mb-2">
                  <p class="text-xs text-gray-400">Genres</p>
                  <button 
                    v-if="selectedGenres.length > 0" 
                    @click="selectedGenres = []" 
                    type="button" 
                    class="text-[10px] text-blue-400 font-bold hover:underline cursor-pointer"
                  >
                    Reset ({{ selectedGenres.length }})
                  </button>
                </div>
                <div class="flex flex-wrap gap-1.5 max-h-56 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-white/20">
                  <button
                    v-for="g in searchGenres"
                    :key="g.id"
                    @click="toggleSearchGenre(g.id)"
                    type="button"
                    class="px-2.5 py-1 rounded-lg text-xs font-semibold transition-all border cursor-pointer select-none"
                    :class="selectedGenres.includes(g.id) 
                      ? 'bg-blue-600 border-blue-500 text-white shadow-md font-bold' 
                      : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:text-white'"
                  >
                    {{ g.name }}
                  </button>
                </div>
              </div>

            </div>
          </div>

        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isLoginOpen" class="fixed inset-0 z-[1000] bg-black/0 flex justify-center items-center p-4" @click.self="isLoginOpen = false">
        <div class="liquidGlass-wrapper w-full max-w-md !rounded-[2rem] shadow-[0_20px_60px_-15px_rgba(0,0,0,1)] relative overflow-hidden">
          <div class="liquidGlass-effect !rounded-[2rem]"></div>
          <div class="liquidGlass-tint !rounded-[2rem]"></div>
          <div class="liquidGlass-shine !rounded-[2rem]"></div>
          <div class="liquidGlass-text w-full p-8 relative z-10">
            <button @click="isLoginOpen = false" class="absolute top-6 right-6 p-2 hover:bg-white/10 rounded-full transition-colors z-20 group"><X class="w-5 h-5 text-white/70 group-hover:text-white" /></button>
            <div class="text-center mb-8">
              <div class="w-16 h-16 rounded-full bg-gradient-to-tr from-blue-500 to-blue-400 p-[2px] mx-auto mb-4 shadow-lg shadow-blue-500/20">
                <div class="w-full h-full rounded-full bg-[#09090b] flex items-center justify-center"><UserIcon class="w-8 h-8 text-white" /></div>
              </div>
              <h2 class="text-3xl font-black tracking-tighter text-white">Welcome Back</h2>
              <p class="text-sm text-white/80 mt-1">Sign in to your Viora account</p>
            </div>
            <form @submit.prevent="handleLogin" class="space-y-5">
              <div>
                <label class="block text-xs font-bold text-white uppercase tracking-wider mb-2">Username</label>
                <input id="viora-username-input" v-model="loginData.username" type="text" class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-white placeholder:text-white/60 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" placeholder="Enter your username" required />
              </div>
              <div>
                <label class="block text-xs font-bold text-white uppercase tracking-wider mb-2">Password</label>
                <div class="relative">
                  <input 
                    v-model="loginData.password" 
                    :type="showPassword ? 'text' : 'password'" 
                    class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 pr-11 text-white placeholder:text-white/60 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" 
                    placeholder="••••••••" 
                    required 
                  />
                  <button 
                    type="button" 
                    @click="showPassword = !showPassword" 
                    class="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/70 hover:text-white transition-colors"
                  >
                    <EyeOff v-if="showPassword" class="w-5 h-5" />
                    <Eye v-else class="w-5 h-5" />
                  </button>
                </div>
              </div>
              <div v-if="loginError" class="text-red-400 text-sm font-medium text-center bg-red-500/10 py-3 rounded-xl border border-red-500/20">{{ loginError }}</div>
              <Button type="submit" :disabled="isLoggingIn" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold h-14 rounded-xl transition-all shadow-lg shadow-blue-600/20 mt-2 flex justify-center items-center">
                <Loader2 v-if="isLoggingIn" class="w-5 h-5 animate-spin mr-2" />
                {{ isLoggingIn ? 'Authenticating...' : 'Sign In' }}
              </Button>
            </form>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div 
        v-if="isProfileOpen" 
        class="fixed inset-0 z-[95] bg-transparent" 
        @click.self="isProfileOpen = false"
      >

        <div 
          class="!absolute top-[80px] right-6 lg:right-12 w-64 rounded-2xl 
                liquidGlass-wrapper
                shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8)] 
                transition-transform duration-200 ease-out"
          :style="glassTransform"
        >
          <div class="liquidGlass-effect !rounded-2xl"></div>
          <div class="liquidGlass-tint !rounded-2xl"></div>
          <div class="liquidGlass-shine !rounded-2xl"></div>
          <div class="liquidGlass-text w-full p-2 relative z-10">

            <div 
              class="absolute inset-0 rounded-2xl pointer-events-none"
              :style="{
                background: `radial-gradient(circle at ${50 + mouseX*30}% ${50 + mouseY*30}%, rgba(255,255,255,0.18), transparent 60%)`
              }"
            ></div>

            <div class="flex items-center gap-3 p-3 mb-2 border-b border-white/10 relative z-10">
              
              <div class="relative w-10 h-10">
                <div class="absolute inset-0 rounded-full bg-gradient-to-tr from-blue-500/60 to-blue-400/60 blur-sm opacity-70"></div>
                <div class="relative w-full h-full rounded-full bg-white/10 border border-white/20 flex items-center justify-center font-bold text-sm text-white shadow-[inset_0_1px_1px_rgba(255,255,255,0.3)]">
                  {{ currentUser.username.charAt(0).toUpperCase() }}
                </div>
              </div>

              <div class="flex-1 min-w-0">
                <h4 class="text-white font-bold text-sm truncate">
                  @{{ currentUser.username }}
                </h4>
                <p class="text-xs text-blue-400 font-medium drop-shadow-[0_0_6px_rgba(96,165,250,0.7)]">
                  Premium Member
                </p>
              </div>
            </div>

            <div class="space-y-1 relative z-10">

             <button
                    @mousemove="(e) => handleMagnetMove(e, 'settings')"
                    @mouseleave="resetMagnet"
                    class="group w-full flex items-center gap-3 p-2.5 text-sm font-medium text-gray-300 rounded-xl transition-all text-left hover:bg-white/10 hover:text-white"
                    :style="activeMagnet === 'settings'
                      ? { transform: `translate(${magneticOffset.x}px, ${magneticOffset.y}px)` }
                      : {}"
                  >
                <Settings class="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
                Account Settings
              </button>

              <!-- Liquid Glass Mode Selector in Profile Dropdown -->
              <div class="px-2 py-2 border-t border-white/10 mt-2 relative z-10">
                <div class="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2 px-1 flex items-center justify-between">
                  <span>Glass Effect</span>
                  <span class="text-blue-400 capitalize">{{ glassMode === 'full' ? 'Full' : glassMode === 'edge' ? 'Edge' : 'Pure' }}</span>
                </div>
                <div class="grid grid-cols-3 gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
                  <button 
                    @click="setGlassMode('full')" 
                    class="py-1.5 px-1 rounded-lg text-[11px] font-semibold transition-all text-center"
                    :class="glassMode === 'full' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-white/10'"
                  >
                    Full
                  </button>
                  <button 
                    @click="setGlassMode('edge')" 
                    class="py-1.5 px-1 rounded-lg text-[11px] font-semibold transition-all text-center"
                    :class="glassMode === 'edge' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-white/10'"
                  >
                    Edge
                  </button>
                  <button 
                    @click="setGlassMode('off')" 
                    class="py-1.5 px-1 rounded-lg text-[11px] font-semibold transition-all text-center"
                    :class="glassMode === 'off' ? 'bg-blue-600 text-white shadow-md' : 'text-gray-400 hover:text-white hover:bg-white/10'"
                  >
                    Pure
                  </button>
                </div>
              </div>

             <button 
                  @click="handleLogout"
                  @mousemove="(e) => handleMagnetMove(e, 'logout')"
                  @mouseleave="resetMagnet"
                  class="group w-full flex items-center gap-3 p-2.5 text-sm font-bold text-red-400 rounded-xl transition-all text-left mt-1 hover:bg-red-500/10 hover:text-red-300"
                  :style="activeMagnet === 'logout'
                    ? { transform: `translate(${magneticOffset.x}px, ${magneticOffset.y}px)` }
                    : {}"
                >
                <LogOut class="w-4 h-4 group-hover:scale-110 transition-transform" />
                Log Out
              </button>

            </div>

          </div>
        </div>
      </div>
    </Transition>

   <header 
      :class="[
        'fixed top-0 w-full z-40 flex items-center justify-between px-6 lg:px-12',
        'transition-[padding,background-color,border-color,box-shadow] duration-500',
        isScrolled 
          ? 'py-3 border-b border-white/10 viora-header-scrolled shadow-[0_8px_32px_rgba(0,0,0,0.3)]' 
          : 'bg-transparent border-b border-transparent py-8'
      ]"
      style="transform: translateZ(0);"
    >

      <h1 
        @click="changeView('home')" 
        class="font-black tracking-tighter flex items-center cursor-pointer"
        :class="isScrolled ? 'text-2xl' : 'text-4xl'"
        style="transition: font-size 0.5s ease;"
      >
        <span class="text-white">V</span>
        <span 
          style="transition: max-width 0.5s ease, opacity 0.5s ease;" 
          class="overflow-hidden"
          :class="isScrolled ? 'max-w-0 opacity-0' : 'max-w-[120px] opacity-100'"
        >
          IORA
        </span>
        <span class="text-blue-400">.</span>
      </h1>

      <div 
        @click="handleUserIconClick" 
        class="relative w-10 h-10 rounded-full cursor-pointer hover:scale-110 transition-transform duration-300"
      >
        <!-- box-shadow glow instead of a blur-md div — GPU composited, zero repaint cost -->
        <div class="w-full h-full rounded-full bg-white/10 border border-white/25 flex items-center justify-center shadow-[inset_0_1px_1px_rgba(255,255,255,0.2),0_0_14px_3px_rgba(96,165,250,0.4)]">
          <span v-if="isLoggedIn" class="font-bold text-sm text-white">
            {{ currentUser.username.charAt(0).toUpperCase() }}
          </span>
          <UserIcon v-else class="w-5 h-5 text-white" />
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
          <div v-for="(movie, index) in activeHeroMovies" :key="movie.id" v-show="index === currentHeroIndex" class="absolute inset-0">
            <img loading="lazy" decoding="async" :src="getImageUrl(movie.backdrop_path, 'original')" class="w-full h-full object-cover opacity-60 scale-100 transition-transform duration-[10s]" :class="index === currentHeroIndex ? 'scale-110' : 'scale-100'" />
            
            <div class="absolute inset-0 bg-gradient-to-t from-[#09090b] via-[#0b1220]/1 to-transparent"></div>
            <div class="absolute inset-0 bg-gradient-to-r from-[#09090b] via-[#0b1220]/1 to-transparent"></div>

            <div class="absolute bottom-[15%] left-6 lg:left-12 max-w-2xl space-y-8 z-10">
              <div class="space-y-6">
                <img loading="lazy" decoding="async" v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w500')" class="max-w-[300px] md:max-w-[480px] max-h-[160px] object-contain drop-shadow-lg" />
                <h2 v-else class="text-5xl lg:text-7xl font-black uppercase  tracking-tighter">{{ movie.title || movie.name }}</h2>
              </div>

              <p class="text-gray-300 text-lg line-clamp-3 max-w-xl font-medium drop-shadow-md leading-relaxed">
                {{ movie.overview }}
              </p>

              <div class="flex items-center gap-4">
                <Button @click="openPlayer(movie)" size="lg" class="bg-white text-black hover:bg-blue-500 hover:text-white font-black px-10 h-12 rounded-xl transition-transform transition-opacity shadow-2xl">
                  <Play class="w-5 h-5  fill-current" /> 
                  <span class="hidden sm:inline">Play</span>
                </Button>

                <Button @click="openInfo(movie)" size="lg" class="bg-gray-500/40 hover:bg-white/20 text-white font-black px-10 h-12 rounded-xl transition-all shadow-2xl ">
                  <Info class="w-5 h-5" /> 
                  <span class="hidden sm:inline">More Info</span>
                </Button>

                <Button @click="handleWatchlistToggle(movie)" variant="outline" class="bg-black/60 border-white/20 hover:bg-white/10 h-12 px-8 rounded-xl font-bold transition-colors">
                  <Check v-if="watchlist.has(movie?.id)" class="w-5 h-5 mr-2 text-green-400" />
                  <Plus v-else class="w-5 h-5 " />
                  <span class="hidden sm:inline">My List</span>
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
          <div class="flex gap-6 overflow-x-auto hide-scrollbar pb-10 pt-4 scroll-smooth hover:shadow-[inset_0_-200px_200px_rgba(59,130,246,0.19)] transition-shadow duration-1200" style="padding-bottom: 20px; padding-top: 40px;">
            <div v-for="movie in watchHistoryMovies" :key="movie.id" @click="openPlayer(movie)" class="relative flex-none w-[300px] md:w-[390px] aspect-video rounded-2xl overflow-hidden bg-[#18181b] transition-transform transition-opacity duration-500 hover:scale-105 hover:-translate-y-1 hover:z-40 hover:shadow-[0_0_60px_rgba(59,130,246,0.18)] transform-gpu will-change-transform group ring-1 ring-white/5 cursor-pointer">
              <div class="skeleton-overlay absolute inset-0 bg-[#27272a]/60 animate-pulse transition-opacity duration-500 z-0"></div>
              <img 
                :src="getImageUrl(movie.backdrop_path || movie.poster_path, movie.backdrop_path ? 'w500' : 'w780')" 
                loading="lazy"
                decoding="async"
                class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-transform transition-opacity duration-700 group-hover:scale-105" 
                style="opacity: 0; transform: scale(1.02);"
                @load="handleImageLoad"
              />
              <div class="absolute inset-0 bg-gradient-to-t   to-transparent p-5 flex flex-col justify-end">
                <div class="mb-2">
                  <img loading="lazy" decoding="async" v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w300')" class="max-w-[140px] max-h-[45px] object-contain drop-shadow-lg transition-transform group-hover:scale-110 origin-left" />
                  <h4 v-else class="text-sm font-black line-clamp-1">{{ movie.title || movie.name }}</h4>
                </div>
                <div class="flex items-center  gap-3 text-[10px] font-black text-gray-400 mt-1 opacity-0 group-hover:opacity-100 transition-transform transition-opacity duration-500 translate-y-2 group-hover:translate-y-0">
                  <div class="px-2 py-0.5 rounded-md flex items-center gap-1 text-[11px] text-white bg-black/60 border border-white/20 shadow-md">
                  <span class=" text-[12px]">{{ (movie.release_date || movie.first_air_date)?.substring(0,4) }}</span>
                 </div> 
                </div>
              </div>
              <div class="absolute bottom-0 left-0 w-full h-1.5 bg-gray-800/80">
                <div class="h-full bg-blue-500" :style="{ width: (movie.progress_percentage || 0) + '%' }"></div>
              </div>
              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 z-30 pointer-events-none">
                <div class="w-14 h-14 bg-white/25 rounded-full flex items-center justify-center border border-white/30">
                  <Lock v-if="!isLoggedIn" class="w-6 h-6 text-white" />
                  <Play v-else class="w-6 h-6 text-white fill-current" />
                </div>
              </div>
              <div class="absolute top-3 right-3 z-20 flex items-center gap-2">
                <button @click.stop="openInfo(movie)" class="p-2 bg-black/60 hover:bg-gray-500/60 rounded-full border border-white/20 transition-colors"><Info class="w-4 h-4 text-white" /></button>
                <button @click.stop="handleWatchlistToggle(movie, movie.media_type)" class="p-2 bg-black/60 hover:bg-blue-500/60 rounded-full border border-white/20 transition-colors"><Check v-if="watchlist.has(movie.id)" class="w-4 h-4 text-green-400" /><Plus v-else class="w-4 h-4 text-white" /></button>
                <button @click.stop="handleRemoveHistory(movie)" class="p-2 bg-black/60 hover:bg-red-600 rounded-full border border-white/20 transition-colors"><X class="w-4 h-4 text-white" /></button>
              </div>
            </div>
          </div>
        </section>

        <section v-for="category in activeCategories" :key="category.id" class="pl-6 lg:pl-12">
          <h3 class="text-2xl font-black mb-8 tracking-tight flex items-center gap-3 "><span class="w-1.5 h-8 bg-blue-500 rounded-full"></span> {{ category.title }}</h3>
          
          <div 
            :class="['flex gap-6 overflow-x-auto hide-scrollbar pb-10 pt-4  hover:shadow-[inset_0_-200px_200px_rgba(59,130,246,0.19)] transition-shadow duration-1200 snap-x', category.layout === 'hero-card' ? 'hero-card-carousel' : '']" 
            style="padding-bottom: 20px; padding-top: 40px;"
            @mouseenter="category.layout === 'hero-card' ? (isHoveringHeroCard = true) : null"
            @mouseleave="category.layout === 'hero-card' ? (isHoveringHeroCard = false) : null"
            @touchstart="category.layout === 'hero-card' ? (isHoveringHeroCard = true) : null"
            @touchend="category.layout === 'hero-card' ? (isHoveringHeroCard = false) : null"
          >
          <div v-for="movie in category.movies" :key="movie.id" @click="openPlayer(movie)" 
              :class="[
                'relative flex-none rounded-2xl overflow-hidden bg-[#18181b] transition-transform transition-opacity duration-500 hover:scale-105 hover:-translate-y-2 hover:z-40 hover:shadow-[0_0_60px_rgba(59,130,246,0.18)] transform-gpu group ring-1 ring-white/5 cursor-pointer snap-center',
                category.layout === 'hero-card' ? 'w-[85vw] md:w-[700px] aspect-video md:aspect-[21/9]' :
                category.layout === 'portrait' ? 'w-[150px] md:w-[220px] aspect-[2/3]' :
                'w-[300px] md:w-[390px] aspect-video'
              ]">
              
              <div class="skeleton-overlay absolute inset-0 bg-[#27272a]/60 animate-pulse transition-opacity duration-500 z-0"></div>
              
              <img :src="getImageUrl(
                 category.layout === 'portrait' ? (movie.poster_path || movie.backdrop_path) : (movie.backdrop_path || movie.poster_path), 
                 category.layout === 'portrait' ? 'w500' : 'w780')" 
                 loading="lazy"
                 decoding="async"
                 class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-transform transition-opacity duration-700 group-hover:scale-105" 
                 style="opacity: 0; transform: scale(1.02);"
                 @load="handleImageLoad"
              />
              
              <div class="absolute inset-0 bg-gradient-to-t to-transparent p-5 md:p-8 flex flex-col justify-end" :class="category.layout === 'portrait' ? 'from-black/90 via-black/40 items-center text-center' : 'from-black/90 via-black/30'">
                <div class="mb-1.5 flex items-center gap-3 flex-wrap" :class="category.layout === 'portrait' ? 'justify-center' : ''">
                  <img loading="lazy" decoding="async" v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w500')" :class="[category.layout === 'hero-card' ? 'max-w-[180px] md:max-w-[280px] max-h-[55px] md:max-h-[75px]' : category.layout === 'portrait' ? 'max-w-[100px] max-h-[35px]' : 'max-w-[140px] max-h-[45px]']" class="object-contain drop-shadow-lg transition-transform group-hover:scale-105 origin-left" />
                  <h4 v-else :class="[category.layout === 'hero-card' ? 'text-xl md:text-3xl font-black' : category.layout === 'portrait' ? 'text-xs md:text-sm line-clamp-2' : 'text-sm md:text-base line-clamp-1']" class="font-black uppercase tracking-tighter drop-shadow-md text-white">{{ movie.title || movie.name }}</h4>

                  <!-- Year Badge ONLY for hero-card layout next to title/logo -->
                  <div v-if="category.layout === 'hero-card' && (movie.release_date || movie.first_air_date)" class="px-2.5 py-0.5 rounded-md flex items-center gap-1 text-[11px] md:text-xs text-white/90 bg-black/60 border border-white/20 shadow-md backdrop-blur-sm font-black">
                    <span>{{ (movie.release_date || movie.first_air_date)?.substring(0,4) }}</span>
                  </div>
                </div>

                <!-- Movie Description for hero-card layout -->
                <p v-if="category.layout === 'hero-card' && movie.overview" class="text-[11px] md:text-xs text-gray-300/90 line-clamp-2 md:line-clamp-3 max-w-lg mb-2 drop-shadow-md font-medium leading-relaxed">
                  {{ movie.overview }}
                </p>

                <!-- Year Badge for non-hero-card layouts (portrait & standard landscape) -->
                <div v-if="category.layout !== 'hero-card'" class="flex items-center gap-3 text-[10px] font-black text-gray-400 mt-1 opacity-0 group-hover:opacity-100 transition-transform transition-opacity duration-500 translate-y-2 group-hover:translate-y-0">
                  <div class="px-2 py-0.5 rounded-md flex items-center gap-1 text-[10px] md:text-[11px] text-white bg-black/60 border border-white/20 shadow-md">
                    <span class="text-[11px] md:text-[12px]">{{ (movie.release_date || movie.first_air_date)?.substring(0,4) }}</span>
                  </div> 
                </div>
              </div>
               
               <div class="absolute top-3 right-3 z-20 flex items-center gap-2">
                 <button @click.stop="openInfo(movie)" class="p-2 bg-black/60 hover:bg-gray-500/60 rounded-full border border-white/20 transition-colors"><Info class="w-3 h-3 md:w-4 md:h-4 text-white" /></button>
                 <button @click.stop="handleWatchlistToggle(movie, movie.media_type)" class="p-2 bg-black/60 hover:bg-blue-500/60 rounded-full border border-white/20 transition-colors"><Check v-if="watchlist.has(movie.id)" class="w-3 h-3 md:w-4 md:h-4 text-green-400" /><Plus v-else class="w-3 h-3 md:w-4 md:h-4 text-white" /></button>
               </div>
             </div>
           </div>
         </section>

         <!-- Featured Studios & Franchises Hub -->
        <section v-if="currentView === 'home'" class="px-6 lg:px-12 py-8 border-t border-b border-white/5 bg-gradient-to-r from-blue-950/20 via-black to-blue-950/20">
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-xl md:text-2xl font-black tracking-tight flex items-center gap-3">
              <span class="w-1.5 h-7 bg-blue-500 rounded-full"></span> Studios & Franchises
            </h3>
            <button 
              @click="isStudiosExpanded = !isStudiosExpanded" 
              class="text-xs text-blue-400 font-bold uppercase tracking-wider flex items-center gap-1.5 hover:text-blue-300 transition-all bg-blue-500/10 hover:bg-blue-500/20 px-3.5 py-1.5 rounded-full border border-blue-500/20 cursor-pointer shadow-sm"
            >
              <span>{{ isStudiosExpanded ? 'Collapse' : 'Lihat Semua (' + studiosList.length + ')' }}</span>
              <ChevronDown class="w-3.5 h-3.5 transition-transform duration-300" :class="isStudiosExpanded ? 'rotate-180' : ''" />
            </button>
          </div>

          <!-- Studio Cards Container: Single Horizontal Row by Default OR Grid when Expanded -->
          <div 
            :class="[
              'transform-gpu transition-all duration-500',
              isStudiosExpanded 
                ? 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3.5' 
                : 'flex gap-3.5 overflow-x-auto hide-scrollbar pb-2 pt-1 scroll-smooth'
            ]"
          >
            <div 
              v-for="st in studiosList" 
              :key="st.id"
              @click="openStudioCollection(st)" 
              :class="[
                'group relative h-20 md:h-24 rounded-2xl overflow-hidden cursor-pointer p-3 flex items-center justify-center border border-white/10 hover:border-blue-500/50 transition-all duration-300 hover:scale-105 bg-[#18181b] hover:bg-[#27272a] shadow-lg transform-gpu will-change-transform',
                isStudiosExpanded ? 'w-full' : 'w-[140px] sm:w-[170px] md:w-[190px] flex-none'
              ]"
            >
              <!-- Compact White Badge ONLY for Marvel -->
              <div v-if="st.id === 'marvel'" class="bg-white rounded-lg px-3 py-1.5 shadow-md flex items-center justify-center transition-transform duration-300 group-hover:scale-105">
                <img 
                  :src="st.logo_path ? getImageUrl(st.logo_path, 'w185') : st.fallback" 
                  :alt="st.name"
                  loading="lazy"
                  decoding="async"
                  class="max-h-8 md:max-h-10 w-auto object-contain pointer-events-none"
                />
              </div>

              <!-- Normal render for other studios -->
              <img 
                v-else
                :src="st.logo_path ? getImageUrl(st.logo_path, 'w185') : st.fallback" 
                :alt="st.name"
                loading="lazy"
                decoding="async"
                :class="[
                  'max-h-10 md:max-h-12 w-auto object-contain transition-transform duration-300 group-hover:scale-110 pointer-events-none transform-gpu',
                  st.invert ? 'filter brightness-0 invert drop-shadow-[0_2px_8px_rgba(255,255,255,0.3)]' : 'drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)]'
                ]"
              />
            </div>
          </div>
        </section>

         <!-- Kidz Zone Section (Clean & Consistent UI) -->
         <section v-if="currentView === 'home' && kidsCategories.length > 0" class="pl-6 lg:pl-12 pt-8 pb-10 space-y-10 border-t border-white/5">
            <!-- Kidz Zone Header Title -->
            <div>
              <h2 class="text-2xl md:text-3xl font-black tracking-tight flex items-center gap-3">
                <span class="w-1.5 h-8 bg-yellow-400 rounded-full"></span> 
                Kidz Zone
                <span class="px-2.5 py-0.5 bg-yellow-400/10 border border-yellow-400/30 text-yellow-400 font-bold text-xs rounded-full ml-1">Safe & Fun</span>
              </h2>
            </div>

            <!-- Kids Categories Lists (Consistent with regular categories) -->
            <div v-for="kidCat in kidsCategories" :key="kidCat.id">
               <h3 class="text-xl md:text-2xl font-black mb-6 tracking-tight flex items-center gap-3">
                 <span class="w-1.5 h-6 bg-blue-500 rounded-full"></span>
                 {{ kidCat.title }}
               </h3>

               <div class="flex gap-6 overflow-x-auto hide-scrollbar pb-6 pt-2 scroll-smooth transform-gpu snap-x">
                  <div 
                    v-for="movie in kidCat.movies" 
                    :key="movie.id" 
                    @click="openPlayer(movie)"
                    :class="[
                      'relative flex-none rounded-2xl overflow-hidden bg-[#18181b] transition-transform transition-opacity duration-500 hover:scale-105 hover:-translate-y-2 hover:z-40 hover:shadow-[0_0_60px_rgba(59,130,246,0.18)] transform-gpu group ring-1 ring-white/5 cursor-pointer snap-center',
                      kidCat.layout === 'portrait' ? 'w-[150px] md:w-[220px] aspect-[2/3]' : 'w-[300px] md:w-[390px] aspect-video'
                    ]"
                  >
                    <!-- Skeleton Overlay -->
                    <div class="skeleton-overlay absolute inset-0 bg-[#27272a]/60 animate-pulse transition-opacity duration-500 z-0"></div>

                    <!-- Poster / Backdrop Image -->
                    <img 
                      :src="getImageUrl(kidCat.layout === 'portrait' ? (movie.poster_path || movie.backdrop_path) : (movie.backdrop_path || movie.poster_path), kidCat.layout === 'portrait' ? 'w500' : 'w780')"
                      loading="lazy"
                      decoding="async"
                      class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-transform transition-opacity duration-700 group-hover:scale-105" 
                      style="opacity: 0; transform: scale(1.02);" 
                      @load="handleImageLoad" 
                      :alt="movie.title || movie.name"
                    />

                    <!-- Overlay Gradient & Info -->
                    <div class="absolute inset-0 bg-gradient-to-t to-transparent p-5 flex flex-col justify-end" :class="kidCat.layout === 'portrait' ? 'from-black/90 via-black/40 items-center text-center' : 'from-black/90 via-black/30'">
                      <div class="mb-1 flex items-center gap-2 flex-wrap" :class="kidCat.layout === 'portrait' ? 'justify-center' : ''">
                        <img loading="lazy" decoding="async" v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w500')" :class="[kidCat.layout === 'portrait' ? 'max-w-[100px] max-h-[35px]' : 'max-w-[140px] max-h-[45px]']" class="object-contain drop-shadow-md transition-transform group-hover:scale-105 origin-left" />
                        <h4 v-else :class="[kidCat.layout === 'portrait' ? 'text-xs md:text-sm line-clamp-2' : 'text-sm md:text-base line-clamp-1']" class="font-black uppercase tracking-tighter drop-shadow-md text-white">{{ movie.title || movie.name }}</h4>
                      </div>
                    </div>

                    <!-- Action Buttons (Info & Watchlist) -->
                    <div class="absolute top-3 right-3 z-20 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                      <button 
                        @click.stop="openInfo(movie)" 
                        class="p-2 bg-black/60 hover:bg-white/20 text-white rounded-full transition-colors border border-white/20"
                        title="Info"
                      >
                         <Info class="w-3.5 h-3.5" />
                      </button>
                      <button 
                        @click.stop="handleWatchlistToggle(movie, movie.media_type)" 
                        class="p-2 bg-black/60 hover:bg-white/20 text-white rounded-full transition-colors border border-white/20"
                        title="Bookmark"
                      >
                        <Check v-if="watchlist.has(movie.id)" class="w-3.5 h-3.5 text-green-400 font-bold" />
                        <Bookmark v-else class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
               </div>
            </div>
         </section>

        <!-- VIORA Monumental Scroll-Driven Typography Reveal (VIORA.) -->
        <section v-if="currentView === 'home'" class="relative pt-28 pb-16 px-4 md:px-8 overflow-hidden border-t border-white/5 bg-black">
          <div class="relative z-10 w-full max-w-[1400px] mx-auto flex flex-col items-center text-center">
            <!-- MONUMENTAL UNIFIED GIANT WORDMARK VIORA. WITH ULTRA-SMOOTH GPU SCROLL REVEAL -->
            <div class="my-8 overflow-hidden py-4 flex items-baseline justify-center select-none transform-gpu gap-1 sm:gap-2 md:gap-3 lg:gap-4">
              <!-- Letters V, I, O, R, A -->
              <div 
                v-for="(letter, idx) in ['V', 'I', 'O', 'R', 'A']" 
                :key="idx"
                class="overflow-hidden inline-flex items-baseline"
              >
                <span 
                  class="text-7xl sm:text-[130px] md:text-[200px] lg:text-[260px] xl:text-[320px] font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white via-slate-100 to-slate-500 transform-gpu will-change-transform cursor-default leading-none block"
                  :style="{
                    transform: `translate3d(0, ${(1 - getLetterProgress(idx, 6)) * 120}%, 0)`,
                    opacity: getLetterProgress(idx, 6) > 0.02 ? getLetterProgress(idx, 6) : 0
                  }"
                >
                  {{ letter }}
                </span>
              </div>

              <!-- CLEAN BLUE DOT . -->
              <div class="overflow-hidden inline-flex items-baseline">
                <span 
                  class="text-6xl sm:text-[110px] md:text-[170px] lg:text-[220px] xl:text-[270px] font-black text-blue-500 transform-gpu will-change-transform leading-none ml-1 sm:ml-2 block"
                  :style="{
                    transform: `translate3d(0, ${(1 - getLetterProgress(5, 6)) * 120}%, 0) scale(${0.6 + getLetterProgress(5, 6) * 0.4})`,
                    opacity: getLetterProgress(5, 6) > 0.02 ? getLetterProgress(5, 6) : 0
                  }"
                >
                  .
                </span>
              </div>
            </div>

            <!-- Footer Bottom Credits -->
            <div class="w-full pt-10 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 font-medium">
              <p>© 2026 VIORA CINEMA INC. ALL RIGHTS RESERVED.</p>
              <div class="flex items-center gap-6 text-slate-400 font-semibold">
                <a href="#" @click.prevent="window.scrollTo({top:0, behavior:'smooth'})" class="hover:text-white transition-colors flex items-center gap-1">Back to Top ↑</a>
              </div>
            </div>
          </div>
        </section>

        <section v-if="currentView !== 'home'" class="px-6 lg:px-12 pt-10 border-t border-white/10 relative">
            <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-10 relative z-30">
              <h2 class="text-3xl md:text-4xl font-black tracking-tight flex items-center gap-4">
                <span class="w-2 h-10 bg-blue-500 rounded-full"></span> 
                Discover <span class="">{{ currentView === 'movie' ? 'Movies' : 'TV Series' }}</span>
              </h2>

              <div class="flex flex-wrap items-center gap-3">
                 <div class="flex items-center bg-white/10 border border-white/15 rounded-xl px-3 py-1">
                   <Filter class="w-4 h-4 text-gray-400 mr-2" />
                   <select v-model="filters.genre" @change="applyFilters" class="bg-transparent text-sm text-white font-medium outline-none cursor-pointer py-2 appearance-none">
                     <option value="" class="bg-[#18181b]">All Genres</option>
                     <option v-for="g in genresList" :key="g.id" :value="g.id" class="bg-[#18181b]">{{g.name}}</option>
                   </select>
                 </div>

                 <div class="flex items-center bg-white/10 border border-white/15 rounded-xl px-3 py-1">
                   <select v-model="filters.country" @change="applyFilters" class="bg-transparent text-sm text-white font-medium outline-none cursor-pointer py-2 appearance-none">
                     <option value="" class="bg-[#18181b]">All Countries</option>
                     <option v-for="c in availableCountries" :key="c.code" :value="c.code" class="bg-[#18181b]">{{ c.name }}</option>
                   </select>
                 </div>

                 <div class="flex items-center bg-white/10 border border-white/15 rounded-xl px-3 py-1">
                   <select v-model="filters.year" @change="applyFilters" class="bg-transparent text-sm text-white font-medium outline-none cursor-pointer py-2 appearance-none">
                     <option value="" class="bg-[#18181b]">All Years</option>
                     <option v-for="y in availableYears" :key="y" :value="y" class="bg-[#18181b]">{{y}}</option>
                   </select>
                 </div>

                 <div class="flex items-center bg-white/10 border border-white/15 rounded-xl px-3 py-1">
                   <select v-model="filters.sortBy" @change="applyFilters" class="bg-transparent text-sm text-white font-medium outline-none cursor-pointer py-2 appearance-none">
                     <option value="popularity.desc" class="bg-[#18181b]">Most Popular</option>
                     <option value="vote_average.desc" class="bg-[#18181b]">Highest Rated</option>
                     <option value="primary_release_date.desc" class="bg-[#18181b]">Newest</option>
                   </select>
                 </div>
              </div>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 auto-rows-max">
              <template v-for="(movie, index) in browseItems" :key="movie.id">
                <!-- Large Horizontal Featured Card (index % 9 === 0) -->
                <div v-if="index % 9 === 0" class="col-span-2 sm:col-span-2 md:col-span-4 lg:col-span-2 relative overflow-hidden rounded-[2rem] bg-[#1a1a1c] p-2 flex flex-col group cursor-pointer ring-1 ring-white/10 hover:ring-white/30 transition-all duration-300 transform-gpu aspect-[4/3] md:aspect-[8/3] lg:aspect-auto lg:h-full" style="content-visibility: auto; contain-intrinsic-size: auto 300px;" @click="openInfo(movie)">
                  
                  <div class="skeleton-overlay absolute inset-2 bg-[#27272a]/60 animate-pulse rounded-[1.5rem] transition-opacity duration-500 z-0 opacity-100 group-hover:opacity-0"></div>
                  
                  <img 
                    :src="getImageUrl(movie.backdrop_path || movie.poster_path, 'w780')" 
                    loading="lazy"
                    decoding="async"
                    class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-in-out z-0 rounded-[1.5rem]" 
                    style="opacity: 0;"  
                    @load="handleImageLoad"
                  />
                  
                  <!-- The Glass Mask -->
                  <div class="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/95 via-black/40 to-transparent z-10 pointer-events-none rounded-b-[1.5rem]"></div>
                  
                  <!-- The Drawer -->
                  <div class="relative z-20 mt-auto p-4 md:p-6 flex flex-col justify-end translate-y-4 group-hover:translate-y-0 transition-transform duration-500 ease-out">
                    <img loading="lazy" decoding="async" 
                      v-if="movie.logo_path" 
                      :src="getImageUrl(movie.logo_path, 'w500')" 
                      class="max-w-[200px] max-h-[70px] object-contain drop-shadow-2xl mb-2 origin-left scale-95 group-hover:scale-100 transition-transform duration-500" 
                    />
                    <h3 
                      v-else 
                      class="text-xl md:text-3xl font-black uppercase tracking-tighter text-white drop-shadow-lg mb-2 line-clamp-2"
                    >
                      {{ movie.title || movie.name }}
                    </h3>
                    <p class="text-[11px] md:text-xs text-gray-300/90 font-medium leading-relaxed line-clamp-2 md:line-clamp-3 mb-4 max-w-md drop-shadow-md opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-100">{{ movie.overview }}</p>
                    <div class="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-500 delay-200">
                       <button class="bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-5 py-2 md:px-6 md:py-2.5 text-white font-bold text-xs md:text-sm transition-colors shadow-lg pointer-events-auto flex items-center gap-2" @click.stop="openPlayer(movie)">
                          <Lock v-if="!isLoggedIn" class="w-4 h-4 md:w-5 md:h-5" />
                          <Play v-else class="w-4 h-4 md:w-5 md:h-5 fill-current" />
                          <span>{{ !isLoggedIn ? 'Locked' : 'Play' }}</span>
                       </button>
                    </div>
                  </div>
                  
                  <!-- Top Right Buttons -->
                  <div class="absolute top-4 right-4 z-20 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <button @click.stop="openInfo(movie)" class="p-1.5 bg-black/60 hover:bg-gray-500/60 rounded-full border border-white/20 transition-colors">
                      <Info class="w-3 h-3 text-white" />
                    </button>
                    <button @click.stop="handleWatchlistToggle(movie)" class="p-1.5 bg-black/60 hover:bg-red-600/80 rounded-full transition-colors border border-white/20">
                      <Check v-if="watchlist.has(movie.id)" class="w-3 h-3 text-green-400" />
                      <Bookmark v-else class="w-3 h-3 text-white" />
                    </button>
                  </div>
                </div>

                <!-- Vertical Card with Expanding Content (Zero Reflow GPU Optimized Illusion) -->
                <div v-else class="col-span-1 relative overflow-hidden rounded-[2rem] bg-[#1a1a1c] p-2 flex flex-col group cursor-pointer ring-1 ring-white/10 hover:ring-white/30 transition-colors duration-300 aspect-[2/3] hover:shadow-[0_0_60px_rgba(59,130,246,0.15)] transform-gpu" style="content-visibility: auto; contain-intrinsic-size: auto 300px;" @click="openInfo(movie)">
                  
                  <!-- Inner Container to clip the image and drawer strictly inside the padding -->
                  <div class="relative w-full h-full rounded-[1.5rem] overflow-hidden transform-gpu">
                    
                    <div class="skeleton-overlay absolute inset-0 bg-[#27272a]/60 animate-pulse transition-opacity duration-500 z-0 opacity-100 group-hover:opacity-0"></div>
                    
                    <!-- Image scales purely via GPU (zero reflow) -->
                    <img 
                      :src="getImageUrl(movie.poster_path || movie.backdrop_path, 'w500')" 
                      loading="lazy"
                      decoding="async"
                      class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out z-0 will-change-transform" 
                      style="opacity: 0;"  
                      @load="handleImageLoad"
                    />
                    
                    <!-- Glass blur mask at the bottom before hover (Fade only, no translate) -->
                    <div class="absolute inset-x-0 bottom-0 h-[40%] bg-gradient-to-t from-black/80 via-black/40 to-transparent z-10 group-hover:opacity-0 transition-opacity duration-500 pointer-events-none will-change-opacity"></div>

                    <!-- The Drawer (Transparent gradient sliding up OVER the image) -->
                    <div class="absolute inset-x-0 bottom-0 p-2 pt-16 flex flex-col justify-end bg-gradient-to-t from-black/95 via-black/70 to-transparent z-20 translate-y-[100%] group-hover:translate-y-0 transition-transform duration-500 ease-out will-change-transform">
                      <img loading="lazy" decoding="async" 
                        v-if="movie.logo_path" 
                        :src="getImageUrl(movie.logo_path, 'w300')" 
                        class="max-w-[120px] max-h-[35px] object-contain drop-shadow-lg opacity-0 -translate-y-4 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-500 origin-left" 
                      />
                      <h4 
                        v-else 
                        class="text-sm md:text-base font-black uppercase tracking-tighter line-clamp-2 text-white opacity-0 -translate-y-4 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-500"
                      >
                        {{ movie.title || movie.name }}
                      </h4>
                      
                      <div class="flex justify-between items-end mt-2 mb-1 opacity-0 translate-y-4 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-500 delay-100">
                         <span class="text-xs font-bold text-gray-300">{{ (movie.release_date || movie.first_air_date)?.substring(0,4) || '' }}</span>
                         <button class="bg-white/10 hover:bg-white/20 border border-white/20 rounded-full px-3 py-1.5 text-white font-bold text-[11px] transition-colors shadow-md pointer-events-auto flex items-center gap-1.5" @click.stop="openPlayer(movie)">
                            <Lock v-if="!isLoggedIn" class="w-3 h-3" />
                            <Play v-else class="w-3 h-3 fill-current" />
                            <span>{{ !isLoggedIn ? 'Locked' : 'Play' }}</span>
                         </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Top Right Action Buttons -->
                  <div class="absolute top-4 right-4 z-20 flex flex-col gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <button @click.stop="openInfo(movie)" class="p-1.5 bg-black/60 hover:bg-gray-500/60 rounded-full border border-white/20 transition-colors">
                      <Info class="w-3 h-3 text-white" />
                    </button>
                    <button @click.stop="handleWatchlistToggle(movie)" class="p-1.5 bg-black/60 hover:bg-red-600/80 rounded-full transition-colors border border-white/20">
                      <Check v-if="watchlist.has(movie.id)" class="w-3 h-3 text-green-400" />
                      <Bookmark v-else class="w-3 h-3 text-white" />
                    </button>
                  </div>
                </div>
              </template>
            </div>

            <div v-if="isBrowseLoading || isFetchingMore" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 mt-6">
              <Skeleton v-for="i in 12" :key="i" :class="['rounded-2xl bg-white/5 animate-pulse', i % 9 === 1 ? 'col-span-2 md:col-span-4 lg:col-span-2 aspect-video' : 'col-span-1 aspect-[2/3]']" />
            </div>

            <!-- Members Only Lock Screen (Bottom) -->
            <div v-if="!isLoggedIn" class="relative z-30 mt-12 py-20 flex flex-col items-center justify-center text-center px-4 space-y-6 border-t border-white/10 bg-gradient-to-t from-black to-transparent">
              <div class="absolute inset-0 bg-[#0a0a0a]/90 -z-10"></div>
              <div class="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-blue-500"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </div>
              <h2 class="text-2xl md:text-4xl font-black tracking-tight text-white">Members Only Area</h2>
              <p class="text-gray-400 text-base md:text-lg max-w-xl">
                Please log in to explore thousands of movies and TV series.
              </p>
              <Button @click="isLoginOpen = true" class="mt-4 bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 h-12 rounded-full shadow-lg shadow-blue-500/20 transition-all hover:scale-105">
                Sign In to Continue
              </Button>
            </div>
        </section>
      </main>
    </div>

    <svg style="display: none">
      <filter
        id="glass-distortion"
        x="0%"
        y="0%"
        width="100%"
        height="100%"
        filterUnits="objectBoundingBox"
      >
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.01 0.01"
          numOctaves="1"
          seed="5"
          result="turbulence"
        />
        <feComponentTransfer in="turbulence" result="mapped">
          <feFuncR type="gamma" amplitude="1" exponent="10" offset="0.5" />
          <feFuncG type="gamma" amplitude="0" exponent="1" offset="0" />
          <feFuncB type="gamma" amplitude="0" exponent="1" offset="0.5" />
        </feComponentTransfer>
        <feGaussianBlur in="turbulence" stdDeviation="3" result="softMap" />
        <feSpecularLighting
          in="softMap"
          surfaceScale="5"
          specularConstant="1"
          specularExponent="100"
          lighting-color="white"
          result="specLight"
        >
          <fePointLight x="-200" y="-200" z="300" />
        </feSpecularLighting>
        <feComposite
          in="specLight"
          operator="arithmetic"
          k1="0"
          k2="1"
          k3="1"
          k4="0"
          result="litImage"
        />
        <feDisplacementMap
          in="SourceGraphic"
          in2="softMap"
          scale="150"
          xChannelSelector="R"
          yChannelSelector="G"
        />
      </filter>
    </svg>

    <div class="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4">
      
      <!-- Search button with Liquid Glass -->
      <div class="liquidGlass-wrapper !rounded-full">
        <div class="liquidGlass-effect !rounded-full"></div>
        <div class="liquidGlass-tint !rounded-full"></div>
        <div class="liquidGlass-shine !rounded-full"></div>
        <div class="liquidGlass-text">
          <button 
            @click="toggleSearch" 
            class="w-[56px] h-[56px] rounded-full flex items-center justify-center bg-transparent transition-all duration-300 hover:scale-110 active:scale-95 group"
            :class="isSearchOpen ? 'text-blue-400' : 'text-gray-400 hover:text-white'"
          >
            <Search class="w-6 h-6 transition-transform group-hover:rotate-12" />
          </button>
        </div>
      </div>

      <!-- Dock navbar with Liquid Glass -->
      <div class="liquidGlass-wrapper dock">
        <div class="liquidGlass-effect dock-layer"></div>
        <div class="liquidGlass-tint dock-layer"></div>
        <div class="liquidGlass-shine dock-layer"></div>
        <div class="liquidGlass-text dock-layer">
          <nav class="relative flex items-center gap-2 p-1.5 rounded-[2rem] overflow-hidden">

            <!-- Sliding Tab Indicator -->
            <div 
              class="absolute top-1 bottom-1 w-12  
                    bg-white/80
                    transition-all duration-800 ease-[cubic-bezier(0.22,1,0.36,1)]"
              :style="sliderStyle"
            ></div>

            <div 
              v-for="(item, index) in navItems" 
              :key="item.key"
              :ref="el => navRefs[index] = el"
              @mouseenter="hoverIndex = index"
              @mousemove="(e) => handleNavMagnet(e, index)"
              @mouseleave="() => { hoverIndex = null; resetNavMagnet(index) }"
              @click="item.action"
              class="relative z-10 p-3 rounded-full cursor-pointer group transition-all"
            >
              
             <Home 
                v-if="item.key === 'home'" 
                class="w-6 h-6 transition-transform duration-200 ease-out"
                :style="activeMagnetIndex === index ? { transform: `translate(${magneticOffsets[index]?.x || 0}px, ${magneticOffsets[index]?.y || 0}px) scale(1.05)` } : {}"
                :class="currentView === 'home' ? 'text-white' : 'text-gray-400 group-hover:text-white'" 
              />

              <Clapperboard 
                v-if="item.key === 'movie'" 
                class="w-6 h-6 transition-transform duration-200 ease-out"
                :style="activeMagnetIndex === index ? { transform: `translate(${magneticOffsets[index]?.x || 0}px, ${magneticOffsets[index]?.y || 0}px) scale(1.05)` } : {}"  
                :class="currentView === 'movie' ? 'text-white' : 'text-gray-400 group-hover:text-white'" 
              />

              <Tv 
                v-if="item.key === 'tv'" 
                class="w-6 h-6 transition-transform duration-200 ease-out"
                :style="activeMagnetIndex === index ? { transform: `translate(${magneticOffsets[index]?.x || 0}px, ${magneticOffsets[index]?.y || 0}px) scale(1.05)` } : {}"
                :class="currentView === 'tv' ? 'text-white' : 'text-gray-400 group-hover:text-white'" 
              />

              <PlayCircle 
                v-if="item.key === 'watchlist'" 
                class="w-6 h-6 transition-transform duration-200 ease-out"
                :style="activeMagnetIndex === index ? { transform: `translate(${magneticOffsets[index]?.x || 0}px, ${magneticOffsets[index]?.y || 0}px) scale(1.05)` } : {}"
                :class="isWatchlistOpen ? 'text-blue-400' : 'text-gray-400 group-hover:text-white'" 
              />

            </div>
          </nav>
        </div>
      </div>

    </div>

    <!-- Studio Collection Modal -->
    <Transition name="fade">
      <div 
        v-if="selectedStudio" 
        class="fixed inset-0 z-[500] bg-black/40 flex justify-center items-center p-4 md:p-8"
        @click.self="selectedStudio = null"
      >
        <div class="w-full max-w-6xl max-h-[90vh] rounded-[2rem] shadow-2xl relative overflow-hidden flex flex-col border border-white/10 bg-[#121215]">
          <div class="w-full flex flex-col relative z-10 h-full overflow-hidden">
            <!-- Modal Header -->
            <div class="p-6 md:p-8 border-b border-white/10 flex justify-between items-center bg-transparent">
            <div>
              <div class="flex items-center gap-4">
                <div class="h-10 md:h-12 px-3 py-1.5 bg-[#f5f5f4] rounded-xl flex items-center justify-center border border-white/20 shadow-md">
                  <img loading="lazy" decoding="async" 
                    :src="selectedStudio.logo_path ? getImageUrl(selectedStudio.logo_path, 'w300') : selectedStudio.fallback" 
                    :alt="selectedStudio.name"
                    class="max-h-8 md:max-h-9 w-auto object-contain"
                  />
                </div>
                <div>
                  <h2 class="text-2xl md:text-3xl font-black text-white tracking-tight">{{ selectedStudio.name }}</h2>
                  <p class="text-xs md:text-sm text-gray-400 mt-0.5">Exclusive movies & TV series collection</p>
                </div>
              </div>
            </div>
            <button 
              @click="selectedStudio = null" 
              class="p-2.5 bg-white/10 hover:bg-red-600 rounded-full transition-all text-white cursor-pointer"
            >
              <X class="w-6 h-6" />
            </button>
          </div>

          <!-- Studio Movies Grid -->
          <div data-lenis-prevent class="flex-1 overflow-y-auto p-6 md:p-8 scrollbar-thin scrollbar-thumb-white/20">
            <div v-if="isFetchingStudio" class="flex justify-center items-center py-20">
              <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
            <div v-else-if="studioMovies.length === 0" class="text-center py-20 text-gray-400">
              No movies found for this studio.
            </div>
            <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              <div 
                v-for="movie in studioMovies" 
                :key="movie.id" 
                @click="openPlayer(movie)"
                class="relative aspect-video rounded-2xl overflow-hidden bg-[#18181b] transition-all duration-500 hover:scale-105 hover:-translate-y-1 hover:z-40 hover:shadow-[0_0_60px_rgba(59,130,246,0.18)] transform-gpu group ring-1 ring-white/10 cursor-pointer"
              >
                <div class="skeleton-overlay absolute inset-0 bg-[#27272a]/60 animate-pulse transition-opacity duration-500 z-0"></div>
                <img 
                  :src="getImageUrl(movie.backdrop_path || movie.poster_path, movie.backdrop_path ? 'w500' : 'w780')" 
                  loading="lazy"
                  decoding="async"
                  class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-all duration-700 group-hover:scale-105" 
                  style="opacity: 0; transform: scale(1.02);"
                  @load="handleImageLoad"
                />
                
                <!-- Bottom Content Overlay -->
                <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent p-4 md:p-5 flex flex-col justify-end">
                  <div class="mb-1">
                    <img loading="lazy" decoding="async" v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w300')" class="max-w-[140px] max-h-[45px] object-contain drop-shadow-lg transition-transform group-hover:scale-110 origin-left" />
                    <h4 v-else class="text-sm md:text-base font-black uppercase tracking-tight line-clamp-1 text-white">{{ movie.title || movie.name }}</h4>
                  </div>
                  
                  <div class="flex items-center gap-3 text-[10px] font-black text-gray-400 mt-1 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
                    <div class="px-2 py-0.5 rounded-md flex items-center gap-1 text-[11px] text-white bg-black/60 border border-white/20 shadow-md">
                      <span>{{ (movie.release_date || movie.first_air_date)?.substring(0,4) }}</span>
                    </div> 
                  </div>
                </div>

                <!-- Hover Center Play Button -->
                <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none z-30">
                  <div class="w-12 h-12 md:w-14 md:h-14 bg-white/25 rounded-full flex items-center justify-center border border-white/30 transform scale-50 group-hover:scale-100 transition-transform">
                    <Lock v-if="!isLoggedIn" class="w-5 h-5 md:w-6 md:h-6 text-white" />
                    <Play v-else class="w-5 h-5 md:w-6 md:h-6 text-white fill-current" />
                  </div>
                </div>

                <!-- Top Right Action Buttons -->
                <div class="absolute top-3 right-3 z-20 flex items-center gap-2">
                  <button @click.stop="openInfo(movie)" class="p-2 bg-black/60 hover:bg-gray-500/60 rounded-full border border-white/20 transition-colors" title="Info">
                    <Info class="w-4 h-4 text-white" />
                  </button>
                  <button @click.stop="handleWatchlistToggle(movie, movie.media_type)" class="p-2 bg-black/60 hover:bg-blue-500/60 rounded-full border border-white/20 transition-colors" title="Bookmark">
                    <Check v-if="watchlist.has(movie.id)" class="w-4 h-4 text-green-400" />
                    <Plus v-else class="w-4 h-4 text-white" />
                  </button>
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>
      </div>
    </Transition>
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

/* LIQUID GLASS STYLES */
.liquidGlass-wrapper {
  position: relative;
  display: flex;
  font-weight: 600;
  overflow: hidden;
  box-shadow: 0 6px 6px rgba(0, 0, 0, 0.2), 0 0 20px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 2.2);
}

.liquidGlass-effect {
  position: absolute;
  z-index: 0;
  inset: 0;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  filter: url(#glass-distortion);
  -webkit-filter: url(#glass-distortion);
  overflow: hidden;
}

/* DYNAMIC GLASS MODES */
.glass-mode-full .liquidGlass-effect {
  filter: url(#glass-distortion) !important;
  -webkit-filter: url(#glass-distortion) !important;
  -webkit-mask-image: none !important;
  mask-image: none !important;
}

.glass-mode-edge .liquidGlass-effect {
  filter: url(#glass-distortion) !important;
  -webkit-filter: url(#glass-distortion) !important;
  -webkit-mask-image: radial-gradient(ellipse at center, transparent 35%, black 80%) !important;
  mask-image: radial-gradient(ellipse at center, transparent 35%, black 80%) !important;
}

.glass-mode-off .liquidGlass-effect {
  filter: none !important;
  -webkit-filter: none !important;
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  background: rgba(255, 255, 255, 0.05) !important;
  -webkit-mask-image: none !important;
  mask-image: none !important;
}

.liquidGlass-tint {
  z-index: 1;
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.12);
}

.liquidGlass-shine {
  position: absolute;
  inset: 0;
  z-index: 2;
  overflow: hidden;
  box-shadow: inset 1px 1px 1px 0 rgba(255, 255, 255, 0.4),
    inset -1px -1px 1px 1px rgba(255, 255, 255, 0.2);
  pointer-events: none;
}

.liquidGlass-text {
  z-index: 3;
  position: relative;
}

.dock,
.dock > .dock-layer {
  border-radius: 2.5rem;
}
</style>