import { Component, ElementRef, ViewChild, inject, signal, OnInit, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-canvas',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="flex flex-col h-screen w-full bg-[#202124] text-white overflow-hidden font-sans">
      
      <!-- TOP BAR (Meeting Info) -->
      <!-- Only visible on hover or active interaction in full screen usually, but kept static for usability -->
      <div class="h-12 flex items-center justify-between px-4 bg-transparent absolute top-0 left-0 right-0 z-50 pointer-events-none">
         <!-- Left: Time / Code -->
         <div class="pointer-events-auto flex items-center gap-4 p-2 rounded-lg bg-[#202124]/60 backdrop-blur-sm mt-2">
            <span class="font-medium text-lg">{{ currentTime }}</span>
            <div class="h-4 w-px bg-white/20"></div>
            <span class="text-sm font-medium text-zinc-300 tracking-wider">{{ meetingCode }}</span>
         </div>

         <!-- Center: Free Plan Warning -->
         <div class="pointer-events-auto px-4 py-1 rounded-full bg-[#3c4043] text-xs font-medium text-yellow-400 flex items-center gap-2 shadow-lg mt-2">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span>Free Plan: Call ends in {{ timeLeft }}</span>
         </div>

         <!-- Right: Connection Status -->
         <div class="pointer-events-auto flex items-center gap-2 mt-2">
             <div class="flex -space-x-2">
                <div *ngFor="let p of participants().slice(0,3)" class="w-8 h-8 rounded-full border-2 border-[#202124] bg-zinc-700 flex items-center justify-center text-xs font-bold" [style.background-color]="p.color">
                   {{ p.name.charAt(0) }}
                </div>
                <div *ngIf="participants().length > 3" class="w-8 h-8 rounded-full border-2 border-[#202124] bg-[#3c4043] flex items-center justify-center text-xs">
                   +{{ participants().length - 3 }}
                </div>
             </div>
         </div>
      </div>

      <!-- MAIN STAGE -->
      <div class="flex-1 flex overflow-hidden relative p-4 gap-4">
         
         <!-- Canvas Container (The "Shared Screen") -->
         <div class="flex-1 relative rounded-lg overflow-hidden bg-[#3c4043] flex flex-col shadow-2xl">
            
            <!-- Whiteboard Header -->
            <div class="h-10 bg-[#202124] flex items-center justify-between px-4 border-b border-[#3c4043]">
               <div class="flex items-center gap-2 text-sm text-zinc-300">
                  <span class="text-green-400 font-bold">● Live</span>
                  <span>Viren's Whiteboard</span>
               </div>
               
               <!-- Quick Tools -->
               <div class="flex items-center bg-[#3c4043] rounded px-1">
                  <button (click)="setColor('#FFFFFF')" class="w-6 h-6 flex items-center justify-center hover:bg-white/10 rounded" [class.bg-white-20]="currentColor === '#FFFFFF'"><div class="w-3 h-3 rounded-full bg-white"></div></button>
                  <button (click)="setColor('#ef4444')" class="w-6 h-6 flex items-center justify-center hover:bg-white/10 rounded" [class.bg-white-20]="currentColor === '#ef4444'"><div class="w-3 h-3 rounded-full bg-red-500"></div></button>
                  <button (click)="setColor('#3b82f6')" class="w-6 h-6 flex items-center justify-center hover:bg-white/10 rounded" [class.bg-white-20]="currentColor === '#3b82f6'"><div class="w-3 h-3 rounded-full bg-blue-500"></div></button>
                  <button (click)="clearCanvas()" class="w-6 h-6 flex items-center justify-center hover:bg-white/10 rounded text-zinc-400 hover:text-white" title="Clear">
                     <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
               </div>
            </div>

            <!-- The Canvas -->
            <div class="flex-1 relative bg-black cursor-crosshair">
                <canvas #outputCanvas 
                    class="absolute inset-0 w-full h-full"
                    (mousedown)="startDrawing($event)"
                    (mousemove)="draw($event)"
                    (mouseup)="stopDrawing()"
                    (mouseleave)="stopDrawing()"
                    (touchstart)="startDrawing($event)"
                    (touchmove)="draw($event)"
                    (touchend)="stopDrawing()">
                </canvas>
                
                <!-- Floating Names (Mock Cursors) -->
                <div class="absolute top-1/4 left-1/3 flex items-center gap-2 pointer-events-none opacity-50 animate-pulse">
                   <svg class="w-4 h-4 text-purple-500 fill-current" viewBox="0 0 24 24"><path d="M5.5 3.5l12 12-4.5 1 4.5 4-2 2-4.5-4-2.5 4.5z"/></svg>
                   <span class="px-2 py-0.5 rounded bg-purple-500 text-[10px] font-bold">Alex</span>
                </div>
            </div>

            <!-- Host Watermark -->
            <div class="absolute bottom-4 left-4 pointer-events-none">
               <div class="px-3 py-1 rounded-full bg-black/50 backdrop-blur text-xs font-medium text-white/70">
                  Viren (You) is presenting
               </div>
            </div>

         </div>

         <!-- SIDEBAR (People/Chat) -->
         <div *ngIf="activeSidebar" class="w-80 bg-[#ffffff] text-black rounded-lg shadow-xl flex flex-col overflow-hidden animate-slide-in">
             <!-- Sidebar Header -->
             <div class="h-14 px-4 border-b flex items-center justify-between">
                <h2 class="font-google-sans text-lg">{{ activeSidebar === 'people' ? 'People' : 'In-call messages' }}</h2>
                <button (click)="toggleSidebar(null)" class="p-2 hover:bg-gray-100 rounded-full">
                   <svg class="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
             </div>

             <!-- PEOPLE LIST -->
             <div *ngIf="activeSidebar === 'people'" class="flex-1 overflow-y-auto p-2">
                 <div class="px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider">In Meeting ({{ participants().length }})</div>
                 
                 <div *ngFor="let p of participants()" class="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg group">
                    <div class="flex items-center gap-3">
                       <div class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold" [style.background-color]="p.color">
                          {{ p.name.charAt(0) }}
                       </div>
                       <div>
                          <div class="text-sm font-medium">{{ p.name }} <span *ngIf="p.isHost" class="text-xs text-gray-500">(Host)</span></div>
                          <div class="text-xs text-gray-500">{{ p.role }}</div>
                       </div>
                    </div>
                    <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <!-- Admin Controls -->
                        <button class="p-1.5 hover:bg-gray-200 rounded-full" title="Mute">
                           <svg class="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                        </button>
                         <button class="p-1.5 hover:bg-gray-200 rounded-full" title="Remove">
                           <svg class="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                        </button>
                    </div>
                 </div>

                 <div class="mt-4 px-4">
                    <button class="w-full py-2 border border-gray-300 rounded text-sm text-blue-600 font-bold hover:bg-blue-50 transition-colors">
                       + Add people
                    </button>
                 </div>
             </div>

             <!-- CHAT LIST -->
             <div *ngIf="activeSidebar === 'chat'" class="flex-1 flex flex-col">
                 <div class="flex-1 p-4 overflow-y-auto space-y-4 bg-gray-50">
                    <div class="bg-[#d1e3fa] text-blue-900 p-3 rounded-lg text-sm mb-4 text-center">
                       Messages can only be seen by people in the call and are deleted when the call ends.
                    </div>
                    
                    <div class="flex flex-col gap-1">
                       <div class="flex items-baseline justify-between">
                          <span class="font-bold text-xs">Alex Chen</span>
                          <span class="text-[10px] text-gray-500">10:42 AM</span>
                       </div>
                       <p class="text-sm">Can you zoom in on the top right corner?</p>
                    </div>

                    <div class="flex flex-col gap-1">
                       <div class="flex items-baseline justify-between">
                          <span class="font-bold text-xs">Sarah Miller</span>
                          <span class="text-[10px] text-gray-500">10:43 AM</span>
                       </div>
                       <p class="text-sm">Love this concept!</p>
                    </div>
                 </div>
                 <div class="p-4 border-t bg-white">
                    <div class="relative">
                       <input type="text" placeholder="Send a message" class="w-full bg-gray-100 rounded-full px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500">
                       <button class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-blue-600 hover:bg-blue-50 rounded-full">
                          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                       </button>
                    </div>
                 </div>
             </div>

         </div>

      </div>

      <!-- BOTTOM BAR (Google Meet Style) -->
      <div class="h-20 bg-[#202124] flex items-center justify-between px-6 shrink-0 relative z-50">
         
         <!-- Left: Info -->
         <div class="w-1/4 flex items-center">
            <div class="font-bold truncate hidden md:block">Daily Standup / Brainstorm</div>
            <span class="md:hidden text-sm truncate">abc-defg-hij</span>
         </div>

         <!-- Center: Controls -->
         <div class="flex items-center gap-2 md:gap-4">
             <!-- Mic -->
             <button (click)="toggleMic()" [class.bg-red-500]="!micOn" [class.bg-zinc-700]="micOn" class="w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center transition-colors hover:bg-zinc-600 text-white shadow-lg border border-white/5">
                <svg *ngIf="micOn" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                <svg *ngIf="!micOn" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18"/></svg>
             </button>

             <!-- Camera -->
             <button (click)="toggleCam()" [class.bg-red-500]="!camOn" [class.bg-zinc-700]="camOn" class="w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center transition-colors hover:bg-zinc-600 text-white shadow-lg border border-white/5">
                <svg *ngIf="camOn" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                <svg *ngIf="!camOn" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3l18 18"/></svg>
             </button>

             <!-- Hand Raise -->
             <button class="w-10 h-10 md:w-12 md:h-12 rounded-full bg-zinc-700 flex items-center justify-center transition-colors hover:bg-zinc-600 text-white shadow-lg border border-white/5" title="Raise hand">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11" /></svg>
             </button>

             <!-- Share Screen -->
             <button class="w-10 h-10 md:w-12 md:h-12 rounded-full bg-zinc-700 flex items-center justify-center transition-colors hover:bg-zinc-600 text-white shadow-lg border border-white/5" title="Present now">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
             </button>

             <!-- End Call -->
             <button (click)="exitSession()" class="w-14 h-10 md:w-16 md:h-12 rounded-full bg-red-600 flex items-center justify-center transition-colors hover:bg-red-700 text-white shadow-lg ml-2" title="Leave call">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M5 3a2 2 0 00-2 2v1c0 8.284 6.716 15 15 15h1a2 2 0 002-2v-3.28a1 1 0 00-.684-.948l-4.493-1.498a1 1 0 00-1.21.502l-1.13 2.257a11.042 11.042 0 01-5.516-5.517l2.257-1.128a1 1 0 00.502-1.21L9.228 3.683A1 1 0 008.279 3H5z" /></svg>
             </button>
         </div>

         <!-- Right: Sidebars -->
         <div class="w-1/4 flex items-center justify-end gap-3">
             <button (click)="shareLink()" class="hidden md:flex items-center gap-2 text-blue-300 hover:text-blue-200 text-sm font-bold mr-4">
                 <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                 Copy Link
             </button>

             <button (click)="toggleSidebar('people')" [class.text-blue-300]="activeSidebar === 'people'" class="p-2 hover:bg-zinc-700 rounded-full transition-colors relative">
                 <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                 <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
             </button>

             <button (click)="toggleSidebar('chat')" [class.text-blue-300]="activeSidebar === 'chat'" class="p-2 hover:bg-zinc-700 rounded-full transition-colors relative">
                 <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                 <span class="absolute top-1 right-1 w-2 h-2 bg-blue-500 rounded-full"></span>
             </button>
         </div>

      </div>

    </div>
  `,
  styles: [`
    .font-google-sans {
      font-family: 'Product Sans', 'Inter', sans-serif;
    }
    @keyframes slideIn {
       from { transform: translateX(100%); opacity: 0; }
       to { transform: translateX(0); opacity: 1; }
    }
    .animate-slide-in {
       animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
  `]
})
export class CanvasComponent implements OnInit, AfterViewInit, OnDestroy {
  @ViewChild('outputCanvas') canvasElement!: ElementRef<HTMLCanvasElement>;
  
  private router = inject(Router);
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private canvasCtx!: CanvasRenderingContext2D;
  private isDrawing = false;
  private sessionId: string | null = null;
  private uploadInFlight = false;
  private readonly frameUploadIntervalMs = 1800;
  private lastFrameUploadMs = 0;
  private readonly resizeHandler = () => this.resizeCanvas();
  
  // UI State
  currentTime = '';
  timeLeft = '40:00';
  meetingCode = 'abc-defg-hij';
  activeSidebar: 'people' | 'chat' | null = null;
  micOn = true;
  camOn = false;

  // Canvas State
  currentColor = '#3b82f6'; // Google Blue default

  // Data
  participants = signal([
    { name: 'Viren Pandey', role: 'Host', isHost: true, color: '#ea4335' }, // Google Red
    { name: 'Alex Chen', role: 'Editor', isHost: false, color: '#a142f4' },
    { name: 'Sarah Miller', role: 'Viewer', isHost: false, color: '#fbbc05' }, // Google Yellow
    { name: 'John Doe', role: 'Viewer', isHost: false, color: '#24c1e0' },
  ]);

  private timeInterval: any;
  private countdownInterval: any;

  ngOnInit() {
     this.updateTime();
     this.timeInterval = setInterval(() => this.updateTime(), 1000);
     this.startCountdown();
     // Random Meeting Code
     this.meetingCode = Math.random().toString(36).substring(2, 5) + '-' + Math.random().toString(36).substring(2, 6) + '-' + Math.random().toString(36).substring(2, 5);
     this.openRemoteSession();
  }

  ngAfterViewInit() {
    this.setupCanvas();
    window.addEventListener('resize', this.resizeHandler);
    
    // Initial resize to fit the flex container
    setTimeout(() => this.resizeCanvas(), 100);
  }

  ngOnDestroy() {
    clearInterval(this.timeInterval);
    clearInterval(this.countdownInterval);
    window.removeEventListener('resize', this.resizeHandler);
    this.closeRemoteSession();
  }

  // --- UI LOGIC ---

  updateTime() {
     const now = new Date();
     this.currentTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  startCountdown() {
    let duration = 40 * 60; // 40 minutes in seconds
    this.countdownInterval = setInterval(() => {
       duration--;
       const m = Math.floor(duration / 60);
       const s = duration % 60;
       this.timeLeft = `${m}:${s < 10 ? '0' : ''}${s}`;
       if (duration <= 0) {
          clearInterval(this.countdownInterval);
          this.timeLeft = '00:00';
          alert('Free plan limit reached.');
          this.exitSession();
       }
    }, 1000);
  }

  toggleSidebar(view: 'people' | 'chat' | null) {
     if (this.activeSidebar === view) {
        this.activeSidebar = null;
     } else {
        this.activeSidebar = view;
        // Trigger resize because canvas container width changes
        setTimeout(() => this.resizeCanvas(), 350); 
     }
  }

  toggleMic() { this.micOn = !this.micOn; }
  toggleCam() { this.camOn = !this.camOn; }

  shareLink() {
     navigator.clipboard.writeText(`https://aircanvas.io/meet/${this.meetingCode}`);
     alert('Meeting link copied to clipboard!');
  }

  // --- CANVAS LOGIC ---

  setupCanvas() {
    const canvas = this.canvasElement.nativeElement;
    // Set internal resolution matches display size
    const rect = canvas.parentElement!.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    
    this.canvasCtx = canvas.getContext('2d')!;
    this.updateCanvasStyle();
  }

  resizeCanvas() {
    if (!this.canvasElement) return;
    const canvas = this.canvasElement.nativeElement;
    const parent = canvas.parentElement!;
    
    // Save current content
    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d')!;
    tempCanvas.width = canvas.width;
    tempCanvas.height = canvas.height;
    tempCtx.drawImage(canvas, 0, 0);

    // Resize
    canvas.width = parent.clientWidth;
    canvas.height = parent.clientHeight;
    
    // Restore and Style
    this.updateCanvasStyle();
    this.canvasCtx.drawImage(tempCanvas, 0, 0);
  }

  updateCanvasStyle() {
    this.canvasCtx.lineWidth = 4;
    this.canvasCtx.lineCap = 'round';
    this.canvasCtx.lineJoin = 'round';
    this.canvasCtx.strokeStyle = this.currentColor;
  }

  setColor(color: string) {
    this.currentColor = color;
    this.canvasCtx.strokeStyle = color;
  }

  startDrawing(e: MouseEvent | TouchEvent) {
    this.isDrawing = true;
    this.canvasCtx.beginPath();
    const { x, y } = this.getCoordinates(e);
    this.canvasCtx.moveTo(x, y);
  }

  draw(e: MouseEvent | TouchEvent) {
    if (!this.isDrawing) return;
    e.preventDefault();
    const { x, y } = this.getCoordinates(e);
    this.canvasCtx.lineTo(x, y);
    this.canvasCtx.stroke();
  }

  stopDrawing() {
    if (!this.isDrawing) return;
    this.isDrawing = false;
    this.canvasCtx.closePath();
    this.captureAndUploadFrame();
  }

  private getCoordinates(e: MouseEvent | TouchEvent): { x: number, y: number } {
    const rect = this.canvasElement.nativeElement.getBoundingClientRect();
    if (e instanceof MouseEvent) {
      return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    } else {
      return { x: e.touches[0].clientX - rect.left, y: e.touches[0].clientY - rect.top };
    }
  }

  clearCanvas() {
    this.canvasCtx.clearRect(0, 0, this.canvasElement.nativeElement.width, this.canvasElement.nativeElement.height);
  }

  exitSession() {
    if(confirm('End the meeting for everyone?')) {
        this.closeRemoteSession();
        this.router.navigate(['/dashboard']);
    }
  }

  private openRemoteSession(): void {
    if (!this.auth.isAuthenticated()) {
      return;
    }
    this.api.startSession(this.auth.user()?.id || '').subscribe({
      next: (session) => {
        this.sessionId = session.id;
      },
      error: (err) => {
        console.warn('[AIRCANVAS] Failed to start backend session', err);
      },
    });
  }

  private closeRemoteSession(): void {
    if (!this.sessionId) {
      return;
    }
    const currentSessionId = this.sessionId;
    this.sessionId = null;
    this.api.endSession(currentSessionId, 0).subscribe({
      error: (err) => {
        console.warn('[AIRCANVAS] Failed to end backend session', err);
      },
    });
  }

  private captureAndUploadFrame(): void {
    if (!this.sessionId || this.uploadInFlight || !this.canvasElement) {
      return;
    }

    const now = Date.now();
    if (now - this.lastFrameUploadMs < this.frameUploadIntervalMs) {
      return;
    }

    this.uploadInFlight = true;
    const canvas = this.canvasElement.nativeElement;
    canvas.toBlob((blob) => {
      if (!blob || !this.sessionId) {
        this.uploadInFlight = false;
        return;
      }

      const brush = `web_color_${this.currentColor.replace('#', '')}`;
      this.api.uploadFrame(this.sessionId, blob, brush, 'free_draw').subscribe({
        next: () => {
          this.lastFrameUploadMs = Date.now();
        },
        error: (err) => {
          console.warn('[AIRCANVAS] Failed to upload frame', err);
        },
        complete: () => {
          this.uploadInFlight = false;
        },
      });
    }, 'image/png', 0.9);
  }
}
