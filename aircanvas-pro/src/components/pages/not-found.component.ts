import { Component } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [NavbarComponent, RouterLink],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white flex flex-col items-center justify-center text-center p-6">
      
      <div class="w-full max-w-lg">
        <div class="text-[120px] font-display font-bold text-zinc-800 leading-none select-none">404</div>
        <h1 class="text-3xl md:text-4xl font-display font-bold mb-4 mt-[-20px] relative z-10">Work in Progress</h1>
        
        <p class="text-xl text-zinc-400 mb-8 leading-relaxed">
          We are working to make this site more better. <br/>
          This page is currently under construction.
        </p>

        <div class="p-6 bg-[#0A0A0C] border border-white/5 rounded-2xl mb-8 transform rotate-2">
           <div class="flex items-center gap-3 mb-2 text-cyan-400 font-mono text-sm">
             <span class="animate-pulse">●</span> SYSTEM STATUS
           </div>
           <p class="text-zinc-500 text-sm font-mono">
             > Building module... <br/>
             > Compiling assets... <br/>
             > Viren Pandey is coding...
           </p>
        </div>

        <a routerLink="/" class="px-8 py-4 bg-white text-black font-bold rounded-lg hover:bg-zinc-200 transition-colors inline-block">
          Return Home
        </a>
      </div>

    </div>
  `
})
export class NotFoundComponent {}