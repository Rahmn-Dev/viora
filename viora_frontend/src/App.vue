<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { Search, Home, Clapperboard, MonitorPlay, Bookmark, Play, Plus, User as UserIcon, Star } from 'lucide-vue-next';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Flame } from 'lucide-vue-next';
const heroMovies = ref([]);
const currentHeroIndex = ref(0);
const movieCategories = ref([]);
const isLoading = ref(true);
const isScrolled = ref(false);
let heroTimer = null;

const API_KEY = import.meta.env.VITE_TMDB_API_KEY;
const BASE_URL = 'https://api.themoviedb.org/3';

// Helper Image Loader dengan wsrv.nl (WebP + Cache)
const getImageUrl = (path, width = 'w780') => {
  if (!path) return '';
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

    // Proses Logo untuk Hero (5 film teratas)
    heroMovies.value = await enrichMoviesWithLogos(trending.data.results.slice(0, 5));

    // Proses Logo untuk semua Kategori (Limit 10 film per kategori biar gak overload API)
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

const handleScroll = () => { isScrolled.value = window.scrollY > 50; };
const startHeroCarousel = () => {
  heroTimer = setInterval(() => {
    currentHeroIndex.value = (currentHeroIndex.value + 1) % heroMovies.value.length;
  }, 8000);
};

onMounted(() => {
  fetchAllData();
  window.addEventListener('scroll', handleScroll);
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  if (heroTimer) clearInterval(heroTimer);
});
</script>

<template>
  <div class="min-h-screen bg-[#09090b] text-white font-sans selection:bg-red-600/30 overflow-x-hidden pb-32">
    
    <header 
      :class="[
        'fixed top-0 w-full z-50 flex items-center justify-between transition-all duration-700 px-6 lg:px-12',
        isScrolled ? 'backdrop-blur-xl py-3 border-b border-white/5 bg-black/20 shadow-2xl' : 'bg-transparent py-8'
      ]"
    >
      <h1 class="font-black tracking-tighter flex items-center cursor-pointer transition-all duration-500" :class="isScrolled ? 'text-2xl' : 'text-4xl'">
        <span class="text-white">V</span>
        <span class="overflow-hidden transition-all duration-500" :class="isScrolled ? 'max-w-0 opacity-0' : 'max-w-[120px] opacity-100'">IORA</span>
        <span class="text-red-600">.</span>
      </h1>

      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-red-600 to-red-400 p-[2px] cursor-pointer hover:scale-110 transition-transform">
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
            
            <div class="absolute inset-0 bg-gradient-to-t from-[#09090b] via-[#09090b]/30 to-transparent"></div>
            <div class="absolute inset-0 bg-gradient-to-r from-[#09090b] via-[#09090b]/50 to-transparent"></div>

            <div class="absolute bottom-[15%] left-6 lg:left-12 max-w-2xl space-y-8 z-10">
              <div class="space-y-6">
                <div class="flex items-center gap-3">
                   <div class="flex items-center bg-[#f5c518] text-black px-2 py-0.5 rounded font-black text-[10px]">IMDb {{ movie.vote_average.toFixed(1) }}</div>
                   <span class="text-red-600 font-bold text-[10px] uppercase tracking-[0.3em]">Viora Originals</span>
                </div>

                <img v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w500')" class="max-w-[300px] md:max-w-[480px] max-h-[160px] object-contain drop-shadow-[0_15px_15px_rgba(0,0,0,0.8)]" />
                <h2 v-else class="text-5xl lg:text-7xl font-black uppercase italic tracking-tighter">{{ movie.title || movie.name }}</h2>
              </div>

              <p class="text-gray-300 text-lg line-clamp-3 max-w-xl font-medium drop-shadow-md leading-relaxed">
                {{ movie.overview }}
              </p>

              <div class="flex items-center gap-4">
                <Button size="lg" class="bg-white text-black hover:bg-red-600 hover:text-white font-black px-10 h-16 rounded-2xl transition-all shadow-2xl">
                  <Play class="w-6 h-6 mr-2 fill-current" /> Play
                </Button>
                <Button size="lg" variant="outline" class="bg-white/10 backdrop-blur-xl border-white/20 hover:bg-white/20 h-16 px-10 rounded-2xl font-bold">
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
            <span class="w-1.5 h-8 bg-red-600 rounded-full"></span>
            {{ category.title }}
          </h3>
          
          <div class="flex gap-6 overflow-x-auto hide-scrollbar pb-10 pt-4 scroll-smooth ">
            <div 
              v-for="movie in category.movies" 
              :key="movie.id"
              class="relative flex-none w-[300px] md:w-[390px] aspect-video rounded-2xl overflow-hidden bg-[#18181b] transition-all duration-500 hover:scale-110 hover:z-50 hover:shadow-lg will-change-transform   transform-gpu  group ring-1 ring-white/5 cursor-pointer"
            >
              <img :src="getImageUrl(movie.backdrop_path, 'w780')" class="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-all duration-700 group-hover:scale-105" />

              <div class="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent p-5 flex flex-col justify-end">
                
                <div class="mb-2">
                  <img v-if="movie.logo_path" :src="getImageUrl(movie.logo_path, 'w300')" class="max-w-[140px] max-h-[45px] object-contain drop-shadow-[0_5px_5px_rgba(0,0,0,0.5)] transition-transform group-hover:scale-110 origin-left" />
                  <h4 v-else class="text-sm md:text-base font-black uppercase italic tracking-tighter line-clamp-1">{{ movie.title || movie.name }}</h4>
                </div>

                <div class="flex items-center gap-3 text-[10px] font-black text-gray-400 mt-1 opacity-0 group-hover:opacity-100 transition-all duration-500 translate-y-2 group-hover:translate-y-0">
                   <div class="bg-[#f5c518] text-black px-1.5 py-0.5 rounded ">IMDb {{ movie.vote_average.toFixed(1) }}</div>
                   <span class="text-white-600">{{ (movie.release_date || movie.first_air_date)?.substring(0,4) }}</span>
                   <div class="bg-[#E97451]/90 text-white px-2 py-0.5 rounded-md flex items-center gap-1 text-[11px] font-bold backdrop-blur-sm">
                      <Flame class="w-3 h-3 opacity-80" />
                      <span>{{ movie.vote_count }}</span>
                    </div>
                </div>
              </div>

              <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300">
                 <div class="w-14 h-14 bg-white/10 backdrop-blur-md rounded-full flex items-center justify-center border border-white/30 transform scale-50 group-hover:scale-100 transition-transform">
                    <Play class="w-6 h-6 text-white fill-current" />
                 </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>

    <nav class="fixed bottom-10 left-1/2 -translate-x-1/2 z-50">

      <div class="flex items-center gap-2 px-4 py-3 bg-[#18181b]/10 backdrop-blur-xl border border-white/10 rounded-full shadow-[0_25px_60px_-12px_rgba(0,0,0,1)]">

      <div class="p-3 rounded-full hover:bg-white/10 transition-all cursor-pointer group">

      <Home class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-all" />

      </div>

      <div class="p-3 rounded-full hover:bg-white/10 transition-all cursor-pointer group">

      <Search class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-all" />

      </div>

      <div class="w-px h-8 bg-white/10 mx-1"></div>

      <div class="p-3 rounded-full hover:bg-white/10 transition-all cursor-pointer group">

      <Clapperboard class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-all" />

      </div>

      <div class="p-3 rounded-full hover:bg-white/10 transition-all cursor-pointer group">

      <MonitorPlay class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-all" />

      </div>

      <div class="p-3 rounded-full hover:bg-white/10 transition-all cursor-pointer group">

      <Bookmark class="w-6 h-6 text-gray-400 group-hover:text-white group-hover:-translate-y-1 transition-all" />

      </div>

      </div>

      </nav>
  </div>
</template>

<style scoped>
.hero-fade-enter-active, .hero-fade-leave-active { transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1); }
.hero-fade-enter-from { opacity: 0; transform: translateY(20px); }
.hero-fade-leave-to { opacity: 0; transform: translateY(-20px); }

.hide-scrollbar::-webkit-scrollbar { display: none; }
.hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>