import { Component } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [NavbarComponent, CommonModule],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      <div class="max-w-4xl mx-auto px-6">
        
        <h1 class="text-5xl md:text-7xl font-display font-bold mb-12">We are <br/> AirCanvas.</h1>
        
        <div class="prose prose-invert prose-lg text-zinc-300 leading-relaxed mb-20">
          <p>
            Founded in 2023, AirCanvas started with a simple question: 
            <span class="text-white font-bold">Why are we still drawing on 2D glass screens when we live in a 3D world?</span>
          </p>
          <p>
            We are a team of designers, engineers, and dreamers obsessed with removing the barriers between thought and creation. By leveraging the latest advancements in computer vision and WebGL, we've built the world's first browser-based spatial drawing tool that requires no specialized hardware—just your hands and your imagination.
          </p>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-white/10 pt-12">
           <div>
              <div class="text-4xl font-bold mb-2">30+</div>
              <div class="text-xs text-zinc-500 uppercase tracking-widest">Team Members</div>
           </div>
           <div>
              <div class="text-4xl font-bold mb-2">100k</div>
              <div class="text-xs text-zinc-500 uppercase tracking-widest">Active Users</div>
           </div>
           <div>
              <div class="text-4xl font-bold mb-2">12</div>
              <div class="text-xs text-zinc-500 uppercase tracking-widest">Patents</div>
           </div>
           <div>
              <div class="text-4xl font-bold mb-2">∞</div>
              <div class="text-xs text-zinc-500 uppercase tracking-widest">Possibilities</div>
           </div>
        </div>

      </div>
    </div>
  `
})
export class AboutComponent {}