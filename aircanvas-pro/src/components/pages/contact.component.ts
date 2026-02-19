import { Component } from '@angular/core';
import { NavbarComponent } from '../ui/navbar.component';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [NavbarComponent, CommonModule],
  template: `
    <app-navbar />
    <div class="min-h-screen bg-[#030304] text-white pt-32 pb-20">
      <div class="max-w-2xl mx-auto px-6">
        
        <div class="text-center mb-12">
          <h1 class="text-4xl font-display font-bold mb-4">Get in touch</h1>
          <p class="text-zinc-400">Have a question about Enterprise plans or custom integrations?</p>
        </div>

        <form class="space-y-6">
           <div class="grid md:grid-cols-2 gap-6">
              <div class="space-y-2">
                 <label class="text-sm font-medium text-zinc-400">First Name</label>
                 <input type="text" class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white focus:border-cyan-500 focus:outline-none transition-colors">
              </div>
              <div class="space-y-2">
                 <label class="text-sm font-medium text-zinc-400">Last Name</label>
                 <input type="text" class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white focus:border-cyan-500 focus:outline-none transition-colors">
              </div>
           </div>

           <div class="space-y-2">
              <label class="text-sm font-medium text-zinc-400">Email Address</label>
              <input type="email" class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white focus:border-cyan-500 focus:outline-none transition-colors">
           </div>

           <div class="space-y-2">
              <label class="text-sm font-medium text-zinc-400">Message</label>
              <textarea rows="6" class="w-full bg-[#0A0A0C] border border-zinc-800 rounded-lg px-4 py-3 text-white focus:border-cyan-500 focus:outline-none transition-colors"></textarea>
           </div>

           <button type="button" class="w-full py-4 bg-white text-black font-bold rounded-lg hover:bg-zinc-200 transition-colors">Send Message</button>
        </form>

      </div>
    </div>
  `
})
export class ContactComponent {}