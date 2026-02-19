import { Component } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-pricing',
  standalone: true,
  imports: [NavbarComponent, RouterLink],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      <div class="max-w-7xl mx-auto px-6">
        
        <div class="text-center mb-20">
          <h1 class="text-5xl md:text-7xl font-display font-bold mb-6 tracking-tight">Simple, transparent pricing</h1>
          <p class="text-xl text-zinc-400 max-w-2xl mx-auto">Plans tailored for your creative journey.</p>
        </div>

        <!-- Empty State / Placeholder -->
        <div class="flex flex-col items-center justify-center py-20 border border-white/5 rounded-2xl bg-[#0A0A0C]">
           <div class="w-16 h-16 bg-zinc-900 rounded-full flex items-center justify-center mb-6">
              <svg class="w-8 h-8 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
           </div>
           <h2 class="text-2xl font-bold mb-2">Pricing tiers are being updated.</h2>
           <p class="text-zinc-500 mb-8 text-center max-w-md">Please check back later or contact our sales team for enterprise inquiries.</p>
           <a routerLink="/contact" class="px-6 py-3 bg-white text-black font-bold rounded-lg hover:bg-zinc-200 transition-colors">Contact Sales</a>
        </div>

      </div>
    </div>
  `
})
export class PricingComponent {}