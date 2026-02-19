import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { NavbarComponent } from '../ui/navbar.component';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [NavbarComponent, RouterLink, NgClass],
  template: `
    <app-navbar />
    
    <main class="w-full relative overflow-hidden bg-[#030304] text-white">
      
      <!-- HERO SECTION -->
      <section class="relative min-h-screen flex flex-col justify-center pt-24 pb-12 overflow-hidden">
        
        <!-- Subtle Organic Background -->
        <div class="absolute inset-0 pointer-events-none opacity-30">
           <div class="absolute top-0 right-0 w-[800px] h-[800px] bg-blue-900/20 rounded-full blur-[120px] translate-x-1/3 -translate-y-1/3"></div>
           <div class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-purple-900/10 rounded-full blur-[100px] -translate-x-1/3 translate-y-1/3"></div>
        </div>

        <div class="max-w-[1400px] mx-auto px-6 w-full relative z-10 grid lg:grid-cols-12 gap-12 items-center">
          
          <!-- Text Content -->
          <div class="lg:col-span-7 flex flex-col justify-center">
            <div class="reveal-up" style="animation-delay: 0.1s;">
               <h1 class="font-display font-extrabold text-7xl md:text-8xl lg:text-9xl tracking-tighter leading-[0.9] mb-8 text-balance">
                 Draw <br/>
                 <span class="text-zinc-500">Beyond</span> <br/>
                 Reality.
               </h1>
            </div>
            
            <div class="reveal-up" style="animation-delay: 0.3s;">
              <p class="text-xl text-zinc-400 max-w-lg mb-10 leading-relaxed font-light">
                The first boundless canvas controlled entirely by gesture and voice. 
                <span class="text-white font-medium">No stylus. No barriers. Just flow.</span>
              </p>
            </div>
            
            <div class="reveal-up flex flex-wrap items-center gap-6" style="animation-delay: 0.5s;">
              <a routerLink="/signup" class="px-8 py-4 bg-white text-black font-bold rounded-lg hover:bg-zinc-200 transition-all duration-300 transform hover:-translate-y-0.5">
                Start Creating
              </a>
              <a routerLink="/features" class="px-8 py-4 border border-zinc-800 hover:border-zinc-600 rounded-lg text-zinc-300 font-medium transition-all duration-300">
                Explore Features
              </a>
            </div>
          </div>

          <!-- Hero Visual: Abstract & Minimal -->
          <div class="lg:col-span-5 h-[500px] lg:h-[700px] relative reveal-up" style="animation-delay: 0.7s;">
            <!-- Abstract floating planes -->
            <div class="absolute inset-0 flex items-center justify-center">
               <div class="w-64 h-80 bg-gradient-to-br from-zinc-800 to-black border border-white/10 rounded-lg shadow-2xl transform -rotate-12 z-10 opacity-80 backdrop-blur-sm"></div>
               <div class="w-64 h-80 bg-zinc-900 border border-white/10 rounded-lg shadow-2xl transform rotate-6 z-20 flex items-center justify-center overflow-hidden">
                  <div class="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10"></div>
                  <img src="https://picsum.photos/400/600" class="w-full h-full object-cover opacity-60 grayscale hover:grayscale-0 transition-all duration-700 ease-out-expo scale-110" alt="Art">
               </div>
               
               <!-- Minimal UI Floating Elements -->
               <div class="absolute top-1/3 -right-4 p-4 bg-[#0A0A0C] border border-white/10 rounded shadow-xl z-30 flex items-center gap-3">
                  <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                  <span class="text-xs font-mono text-zinc-400">REC 00:04:12</span>
               </div>
            </div>
          </div>
        </div>
      </section>

      <!-- BRAND MARQUEE -->
      <section class="border-y border-white/5 bg-[#050505] py-12">
        <div class="max-w-[1400px] mx-auto px-6">
          <p class="text-center text-xs font-mono text-zinc-600 mb-8 uppercase tracking-widest">Powering creativity at</p>
          <div class="flex justify-center flex-wrap gap-12 md:gap-20 opacity-40 grayscale mix-blend-screen">
             <div class="font-display font-bold text-xl tracking-tighter">PIXAR</div>
             <div class="font-display font-bold text-xl tracking-tighter">FIGMA</div>
             <div class="font-display font-bold text-xl tracking-tighter">EPIC GAMES</div>
             <div class="font-display font-bold text-xl tracking-tighter">UNITY</div>
             <div class="font-display font-bold text-xl tracking-tighter">WETA</div>
          </div>
        </div>
      </section>

      <!-- FEATURES / BENTO GRID -->
      <section id="features" class="py-32 bg-[#030304]">
        <div class="max-w-[1400px] mx-auto px-6">
          <div class="mb-24 max-w-2xl">
            <h2 class="text-4xl md:text-5xl font-display font-bold mb-6 tracking-tight">Engineered for <br/> <span class="text-zinc-500">Flow State.</span></h2>
            <p class="text-zinc-400 text-lg">We stripped away the interface to let you focus purely on the act of creation. It's not just a tool; it's an extension of your mind.</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[400px]">
            
            <!-- Large Card -->
            <div class="md:col-span-2 rounded-2xl bg-[#0A0A0C] border border-white/5 p-10 relative overflow-hidden group">
               <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/80 z-10"></div>
               <img src="https://picsum.photos/1200/800" class="absolute inset-0 w-full h-full object-cover opacity-40 group-hover:scale-105 transition-transform duration-1000 ease-out-expo" alt="Gesture">
               <div class="relative z-20 h-full flex flex-col justify-end">
                 <h3 class="text-3xl font-display font-bold mb-2">Air Gestures</h3>
                 <p class="text-zinc-400 max-w-md">Precise hand tracking allows you to manipulate the canvas in 3D space without touching a screen.</p>
               </div>
            </div>

            <!-- Tall Card -->
            <div class="md:col-span-1 rounded-2xl bg-[#0A0A0C] border border-white/5 p-10 relative overflow-hidden group">
               <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-blue-900/20 to-transparent"></div>
               <div class="relative z-20 h-full flex flex-col justify-between">
                 <div class="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
                    <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                 </div>
                 <div>
                    <h3 class="text-2xl font-display font-bold mb-2">Voice Command</h3>
                    <p class="text-zinc-400 text-sm">Say "New Layer" or "Switch Brush" to keep your rhythm unbroken.</p>
                 </div>
               </div>
            </div>

            <!-- Medium Card -->
            <div class="md:col-span-1 rounded-2xl bg-[#0A0A0C] border border-white/5 p-10 relative overflow-hidden group">
               <div class="relative z-20 h-full flex flex-col justify-between">
                  <div class="flex gap-2">
                     <div class="w-3 h-3 rounded-full bg-red-500/50"></div>
                     <div class="w-3 h-3 rounded-full bg-yellow-500/50"></div>
                     <div class="w-3 h-3 rounded-full bg-green-500/50"></div>
                  </div>
                  <div>
                    <h3 class="text-2xl font-display font-bold mb-2">Zero UI</h3>
                    <p class="text-zinc-400 text-sm">Interface elements only appear when you look for them. Maximum canvas, minimal clutter.</p>
                 </div>
               </div>
            </div>

             <!-- Medium Card with Graphic -->
            <div class="md:col-span-2 rounded-2xl bg-[#0A0A0C] border border-white/5 p-10 relative overflow-hidden group flex items-center">
               <div class="absolute right-0 top-0 w-1/2 h-full bg-gradient-to-l from-zinc-900 to-transparent"></div>
               <div class="relative z-20 w-1/2">
                  <h3 class="text-3xl font-display font-bold mb-4">Real-time <br/> Collaboration</h3>
                  <p class="text-zinc-400 mb-6">Invite your team into your room. Draw together on the same 3D model with zero latency.</p>
                  <a routerLink="/features" class="text-white border-b border-white pb-1 hover:text-zinc-300 hover:border-zinc-300 transition-colors">See how it works</a>
               </div>
               <div class="absolute right-10 top-1/2 -translate-y-1/2 w-64 h-64 opacity-50">
                  <!-- Abstract geometric shape -->
                  <div class="w-full h-full border border-white/10 rounded-full flex items-center justify-center">
                     <div class="w-3/4 h-3/4 border border-white/10 rounded-full"></div>
                  </div>
               </div>
            </div>

          </div>
        </div>
      </section>

      <!-- TESTIMONIALS (Minimal) -->
      <section id="testimonials" class="py-32 border-t border-white/5">
        <div class="max-w-[1400px] mx-auto px-6">
           <div class="grid md:grid-cols-2 gap-16 items-start">
             <div>
                <h2 class="text-4xl font-display font-bold mb-12">Designed for the <br/> world's best.</h2>
             </div>
             <div class="space-y-12">
                <div class="group">
                  <p class="text-2xl leading-relaxed text-zinc-300 mb-6">"The first time I used AirCanvas, I felt like I was drawing inside my own mind. It's not software; it's a superpower."</p>
                  <div class="flex items-center gap-4">
                     <div class="w-10 h-10 bg-zinc-800 rounded-full overflow-hidden">
                       <img src="https://picsum.photos/100/100?random=1" class="w-full h-full object-cover">
                     </div>
                     <div>
                       <div class="font-bold text-sm">Alex Chen</div>
                       <div class="text-xs text-zinc-500">Lead Artist, Pixar</div>
                     </div>
                  </div>
                </div>
                 <div class="h-px bg-white/5 w-full"></div>
                 <div class="group">
                  <p class="text-2xl leading-relaxed text-zinc-300 mb-6">"Finally, a tool that respects the Z-axis. My architectural sketches have never been this fluid."</p>
                  <div class="flex items-center gap-4">
                     <div class="w-10 h-10 bg-zinc-800 rounded-full overflow-hidden">
                       <img src="https://picsum.photos/100/100?random=2" class="w-full h-full object-cover">
                     </div>
                     <div>
                       <div class="font-bold text-sm">Sarah Miller</div>
                       <div class="text-xs text-zinc-500">Concept Designer</div>
                     </div>
                  </div>
                </div>
             </div>
           </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="py-40 bg-[#0A0A0C] relative overflow-hidden text-center">
         <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-80 z-10"></div>
         
         <div class="relative z-20 max-w-4xl mx-auto px-6">
            <h2 class="font-display font-extrabold text-6xl md:text-8xl tracking-tighter mb-12">
              Start your <br/> masterpiece.
            </h2>
            <div class="flex flex-col sm:flex-row items-center justify-center gap-6">
               <a routerLink="/signup" class="w-full sm:w-auto px-10 py-5 bg-white text-black font-bold text-lg rounded-lg hover:bg-zinc-200 transition-colors duration-300">
                  Create Free Account
               </a>
               <a routerLink="/pricing" class="w-full sm:w-auto px-10 py-5 border border-white/20 hover:border-white text-zinc-300 hover:text-white font-medium text-lg rounded-lg transition-colors duration-300">
                  View Pricing
               </a>
            </div>
            <p class="mt-8 text-zinc-500 text-sm">No credit card required. 14-day free trial on Pro plans.</p>
         </div>
      </section>

      <footer class="bg-black py-20 border-t border-white/5 text-zinc-500 text-sm">
        <div class="max-w-[1400px] mx-auto px-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12">
           <div class="col-span-2 lg:col-span-2">
              <div class="font-display font-bold text-white text-xl mb-6">AirCanvas</div>
              <p class="max-w-xs mb-8">Redefining digital creation through spatial computing and natural language processing.</p>
              <div class="flex gap-6">
                 <a href="#" class="hover:text-white transition-colors">Twitter</a>
                 <a href="#" class="hover:text-white transition-colors">Instagram</a>
                 <a href="#" class="hover:text-white transition-colors">LinkedIn</a>
              </div>
           </div>
           
           <div class="flex flex-col gap-4">
              <h4 class="font-bold text-white mb-2">Product</h4>
              <a routerLink="/features" class="hover:text-white transition-colors">Features</a>
              <a routerLink="/pricing" class="hover:text-white transition-colors">Pricing</a>
              <a routerLink="/404" class="hover:text-white transition-colors">Enterprise</a>
              <a routerLink="/404" class="hover:text-white transition-colors">Changelog</a>
           </div>

           <div class="flex flex-col gap-4">
              <h4 class="font-bold text-white mb-2">Resources</h4>
              <a routerLink="/404" class="hover:text-white transition-colors">Documentation</a>
              <a routerLink="/404" class="hover:text-white transition-colors">API Reference</a>
              <a routerLink="/404" class="hover:text-white transition-colors">Community</a>
              <a routerLink="/404" class="hover:text-white transition-colors">Help Center</a>
           </div>

           <div class="flex flex-col gap-4">
              <h4 class="font-bold text-white mb-2">Company</h4>
              <a routerLink="/about" class="hover:text-white transition-colors">About</a>
              <a routerLink="/blog" class="hover:text-white transition-colors">Blog</a>
              <a routerLink="/careers" class="hover:text-white transition-colors">Careers</a>
              <a routerLink="/contact" class="hover:text-white transition-colors">Contact</a>
           </div>
        </div>
        <div class="max-w-[1400px] mx-auto px-6 mt-20 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4">
           <div>© 2023 AirCanvas Inc. Made with love by Viren Pandey.</div>
           <div class="flex gap-6">
              <a routerLink="/privacy" class="hover:text-white">Privacy</a>
              <a routerLink="/terms" class="hover:text-white">Terms</a>
           </div>
        </div>
      </footer>
    </main>
  `
})
export class LandingComponent {}