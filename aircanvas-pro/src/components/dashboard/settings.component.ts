import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SidebarComponent } from '../ui/sidebar.component';
import { AuthService } from '../../services/auth.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, SidebarComponent, FormsModule],
  template: `
    <div class="flex min-h-screen w-full bg-[#030304] text-white font-sans">
      <app-sidebar />
      <main class="flex-1 flex flex-col relative bg-[#030304] pl-20 lg:pl-72 transition-all duration-300">
        <div class="p-8 max-w-3xl">
            <h1 class="text-4xl font-display font-bold mb-8">Settings</h1>
            
            <div class="space-y-8">
                <!-- Profile Section -->
                <section class="p-6 rounded-2xl bg-[#0A0A0C] border border-white/5">
                    <h2 class="text-xl font-bold mb-4">Profile Settings</h2>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm text-zinc-400 mb-1">Display Name</label>
                            <input type="text" [value]="auth.user()?.name" class="w-full bg-zinc-900 border border-zinc-800 rounded px-4 py-2 text-white focus:border-cyan-500 outline-none">
                        </div>
                         <div>
                            <label class="block text-sm text-zinc-400 mb-1">Email</label>
                            <input type="email" [value]="auth.user()?.email" disabled class="w-full bg-zinc-900/50 border border-zinc-800 rounded px-4 py-2 text-zinc-500 cursor-not-allowed">
                        </div>
                    </div>
                </section>

                <!-- Application Settings -->
                 <section class="p-6 rounded-2xl bg-[#0A0A0C] border border-white/5">
                    <h2 class="text-xl font-bold mb-4">Application Preferences</h2>
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="font-medium">Dark Mode</div>
                                <div class="text-xs text-zinc-500">Always active in AirCanvas Pro</div>
                            </div>
                            <div class="w-10 h-6 bg-cyan-600 rounded-full relative cursor-pointer">
                                <div class="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow"></div>
                            </div>
                        </div>
                         <div class="flex items-center justify-between">
                            <div>
                                <div class="font-medium">Gesture Sensitivity</div>
                                <div class="text-xs text-zinc-500">Adjust hand tracking precision</div>
                            </div>
                            <input type="range" class="accent-cyan-500">
                        </div>
                         <div class="flex items-center justify-between">
                            <div>
                                <div class="font-medium">Voice Commands</div>
                                <div class="text-xs text-zinc-500">Enable "Hey Canvas" trigger</div>
                            </div>
                            <div class="w-10 h-6 bg-cyan-600 rounded-full relative cursor-pointer">
                                <div class="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow"></div>
                            </div>
                        </div>
                    </div>
                </section>

                <section class="p-6 rounded-2xl bg-[#0A0A0C] border border-white/5">
                    <h2 class="text-xl font-bold mb-2">Python UI Connection</h2>
                    <p class="text-sm text-zinc-400 mb-4">
                        Use this same account with the desktop Python runtime so both frontends share sessions and frame storage.
                    </p>

                    <div class="mb-4">
                        <div class="text-xs text-zinc-500 mb-1">Backend Base URL</div>
                        <div class="font-mono text-sm bg-zinc-900 border border-zinc-800 rounded px-3 py-2 break-all">
                            {{ auth.apiBaseUrl() }}
                        </div>
                    </div>

                    <div class="text-xs text-zinc-500 mb-1">.env block for desktop app</div>
                    <pre class="font-mono text-xs bg-zinc-900 border border-zinc-800 rounded px-3 py-3 whitespace-pre-wrap break-all">{{ auth.pythonEnvHint() }}</pre>

                    <div class="mt-4 flex flex-wrap gap-3">
                        <button (click)="copyPythonEnv()" class="px-4 py-2 bg-cyan-600 text-white font-bold rounded hover:bg-cyan-500 transition-colors">
                            {{ copyButtonLabel }}
                        </button>
                        <a
                            [href]="auth.apiBaseUrl() + '/dashboard'"
                            target="_blank"
                            rel="noreferrer"
                            class="px-4 py-2 bg-white/10 border border-white/10 text-white font-semibold rounded hover:bg-white/20 transition-colors"
                        >
                            Open Backend Dashboard
                        </a>
                    </div>
                </section>
                
                <div class="flex justify-end">
                    <button class="px-6 py-2 bg-white text-black font-bold rounded hover:bg-zinc-200 transition-colors">Save Changes</button>
                </div>
            </div>
        </div>
      </main>
    </div>
  `
})
export class SettingsComponent {
    auth = inject(AuthService);
    copyButtonLabel = 'Copy .env Block';

    async copyPythonEnv(): Promise<void> {
        try {
            await navigator.clipboard.writeText(this.auth.pythonEnvHint());
            this.copyButtonLabel = 'Copied';
            setTimeout(() => {
                this.copyButtonLabel = 'Copy .env Block';
            }, 1800);
        } catch {
            this.copyButtonLabel = 'Copy Failed';
            setTimeout(() => {
                this.copyButtonLabel = 'Copy .env Block';
            }, 1800);
        }
    }
}
