import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from '../ui/sidebar.component';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, SidebarComponent],
  template: `
    <div class="flex min-h-screen w-full bg-[#030304] text-white font-sans">
      <app-sidebar />
      <main class="flex-1 flex flex-col relative bg-[#030304] pl-20 lg:pl-72 transition-all duration-300">
        <div class="p-8">
            
            <!-- Header -->
            <div class="flex flex-col md:flex-row items-end gap-6 mb-12">
                <div class="w-32 h-32 rounded-full bg-zinc-800 border-2 border-white/10 flex items-center justify-center text-4xl font-bold shadow-2xl">
                    {{ auth.user()?.name?.charAt(0) }}
                </div>
                <div class="mb-4">
                    <h1 class="text-4xl font-display font-bold">{{ auth.user()?.name }}</h1>
                    <p class="text-zinc-400 mb-2">{{ auth.user()?.email }}</p>
                    <div class="flex gap-4 mt-4">
                        <div class="text-sm px-3 py-1 bg-white/5 rounded-full border border-white/5"><span class="font-bold text-white">0</span> Projects</div>
                        <div class="text-sm px-3 py-1 bg-white/5 rounded-full border border-white/5"><span class="font-bold text-white">0</span> Followers</div>
                        <div class="text-sm px-3 py-1 bg-white/5 rounded-full border border-white/5"><span class="font-bold text-white">0</span> Following</div>
                    </div>
                </div>
            </div>

            <div class="h-px bg-white/5 w-full mb-12"></div>

            <h2 class="text-2xl font-bold mb-6">Recent Work</h2>
            
            <div class="flex flex-col items-center justify-center py-20 border border-white/5 rounded-xl bg-[#0A0A0C]">
                <p class="text-zinc-500">No projects created yet.</p>
            </div>

        </div>
      </main>
    </div>
  `
})
export class ProfileComponent {
    auth = inject(AuthService);
}