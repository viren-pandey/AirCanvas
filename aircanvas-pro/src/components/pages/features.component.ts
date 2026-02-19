import { Component } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-features',
  standalone: true,
  imports: [NavbarComponent, CommonModule],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      
      <!-- Header -->
      <div class="max-w-7xl mx-auto px-6 mb-24 text-center">
        <h1 class="text-5xl md:text-7xl font-display font-bold mb-6">Tools for the <br/> Spatial Era</h1>
        <p class="text-xl text-zinc-400 max-w-2xl mx-auto">AirCanvas isn't just a drawing app. It's a complete spatial operating system for creativity.</p>
      </div>

      <!-- Feature Grid -->
      <div class="max-w-7xl mx-auto px-6">
         
         <div class="grid md:grid-cols-2 gap-12 mb-32 items-center">
            <div class="order-2 md:order-1">
               <h2 class="text-3xl font-bold mb-4">6DOF Hand Tracking</h2>
               <p class="text-zinc-400 leading-relaxed mb-6">Our proprietary CV engine tracks 21 points on each hand at 60fps. Whether you're pinching to zoom or grasping a virtual brush, the response is instant and natural.</p>
               <ul class="space-y-2 text-zinc-300">
                  <li class="flex items-center gap-3"><span class="text-cyan-500">✓</span> Sub-millimeter precision</li>
                  <li class="flex items-center gap-3"><span class="text-cyan-500">✓</span> Occlusion handling</li>
                  <li class="flex items-center gap-3"><span class="text-cyan-500">✓</span> Low latency WebGL rendering</li>
               </ul>
            </div>
            <div class="order-1 md:order-2 h-80 bg-zinc-900 rounded-2xl border border-white/5 overflow-hidden relative">
               <img src="https://picsum.photos/800/600?random=10" class="w-full h-full object-cover opacity-60">
            </div>
         </div>

         <div class="grid md:grid-cols-2 gap-12 mb-32 items-center">
             <div class="h-80 bg-zinc-900 rounded-2xl border border-white/5 overflow-hidden relative">
               <img src="https://picsum.photos/800/600?random=11" class="w-full h-full object-cover opacity-60">
            </div>
            <div>
               <h2 class="text-3xl font-bold mb-4">Voice Macros</h2>
               <p class="text-zinc-400 leading-relaxed mb-6">Keep your hands on the canvas. Use voice commands to switch tools, change colors, or export your work. It's like having an assistant in the studio.</p>
               <div class="flex gap-3">
                  <span class="px-3 py-1 rounded bg-white/10 text-xs border border-white/10">"Select Circle"</span>
                  <span class="px-3 py-1 rounded bg-white/10 text-xs border border-white/10">"Clear Canvas"</span>
                  <span class="px-3 py-1 rounded bg-white/10 text-xs border border-white/10">"Save Project"</span>
               </div>
            </div>
         </div>

      </div>

    </div>
  `
})
export class FeaturesComponent {}