import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  template: `
    <nav class="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[#030304]/80 backdrop-blur-xl transition-all duration-500">
      <div class="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
        <!-- Logo -->
        <a routerLink="/" class="flex items-center gap-3 group">
          <div class="w-6 h-6 bg-white rounded-sm flex items-center justify-center">
             <div class="w-2 h-2 bg-black rounded-full"></div>
          </div>
          <span class="font-display font-bold text-lg tracking-tight text-white">AirCanvas</span>
        </a>

        <!-- Desktop Links -->
        <div class="hidden md:flex items-center gap-8">
          <a routerLink="/pricing" routerLinkActive="text-white" class="text-sm font-medium text-zinc-400 hover:text-white transition-colors duration-300">Pricing</a>
          <a routerLink="/blog" routerLinkActive="text-white" class="text-sm font-medium text-zinc-400 hover:text-white transition-colors duration-300">Blog</a>
          <a routerLink="/careers" routerLinkActive="text-white" class="text-sm font-medium text-zinc-400 hover:text-white transition-colors duration-300">Careers</a>
        </div>

        <!-- Auth Buttons -->
        <div class="flex items-center gap-4">
          @if (auth.isAuthenticated()) {
            @if (auth.isAdmin()) {
               <a routerLink="/admin-main" class="text-sm font-bold text-cyan-400 hover:text-cyan-300 transition-colors">
                  Admin Panel
               </a>
            }
            <a routerLink="/dashboard" class="text-sm font-medium text-white hover:text-zinc-300 transition-colors">
              Dashboard
            </a>
          } @else {
            <a routerLink="/login" class="hidden md:block text-sm font-medium text-zinc-400 hover:text-white transition-colors">Log In</a>
            <a routerLink="/signup" class="px-5 py-2 rounded-lg bg-white text-black text-sm font-semibold hover:bg-zinc-200 transition-colors duration-300">
              Start Free
            </a>
          }
        </div>
      </div>
    </nav>
  `
})
export class NavbarComponent {
  auth = inject(AuthService);
}