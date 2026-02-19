"""
voice_listener.py — 4.0
-----------------------
Robust threaded voice listener with:
  • Command queue (thread-safe)
  • Calibrates ambient noise on start
  • Graceful degradation if SpeechRecognition not installed
  • Logs confidence (Google API returns text, not confidence; we mark all as 1.0)
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Optional

try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False


class VoiceListener:

    def __init__(
        self,
        language:         str   = "en-US",
        energy_threshold: int   = 280,
        pause_threshold:  float = 0.5,
        phrase_limit:     float = 5.0,
    ) -> None:
        self._lang        = language
        self._energy      = energy_threshold
        self._pause       = pause_threshold
        self._phrase_lim  = phrase_limit
        self._queue: queue.Queue[str] = queue.Queue(maxsize=30)
        self._running     = False
        self._thread: Optional[threading.Thread] = None
        self._available   = _SR_AVAILABLE
        self._error: Optional[str] = None
        if not _SR_AVAILABLE:
            self._error = "SpeechRecognition not installed"

    @property
    def available(self) -> bool:
        return self._available

    @property
    def error(self) -> Optional[str]:
        return self._error

    def start(self) -> bool:
        if not self._available:
            print(f"[VOICE] {self._error}")
            return False
        if self._running:
            return True
        # Preflight microphone access so UI doesn't show MIC ON when startup fails.
        try:
            with sr.Microphone():
                pass
        except Exception as e:
            self._available = False
            self._error = f"Microphone: {e}"
            print(f"[VOICE] {self._error}")
            return False
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True, name="VoiceListener")
        self._thread.start()
        print("[VOICE] Listening — say 'Canvas, <command>' or just 'Stop'")
        return True

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_text(self) -> Optional[str]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _loop(self) -> None:
        rec = sr.Recognizer()
        rec.energy_threshold        = self._energy
        rec.pause_threshold         = self._pause
        rec.dynamic_energy_threshold = True

        try:
            mic = sr.Microphone()
        except Exception as e:
            self._available = False
            self._error     = f"Microphone: {e}"
            print(f"[VOICE] {self._error}")
            return

        with mic as src:
            try:
                rec.adjust_for_ambient_noise(src, duration=1.0)
                print("[VOICE] Noise calibrated. Ready.")
            except Exception:
                pass

        while self._running:
            try:
                with mic as src:
                    audio = rec.listen(src, timeout=2.0, phrase_time_limit=self._phrase_lim)
                try:
                    text = rec.recognize_google(audio, language=self._lang).lower().strip()
                    if text and not self._queue.full():
                        self._queue.put_nowait(text)
                        print(f"[VOICE] '{text}'")
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"[VOICE] API error: {e}")
                    time.sleep(1.0)
            except sr.WaitTimeoutError:
                pass
            except Exception as e:
                print(f"[VOICE] Error: {e}")
                time.sleep(0.4)
