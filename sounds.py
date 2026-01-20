"""Sound effects system for Chess Learner."""
import pygame
import numpy as np
import os
from typing import Dict, Optional


class SoundSystem:
    """Manages sound effects with generated defaults and custom file support."""

    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.muted = False
        self._load_sounds()

    def _load_sounds(self):
        """Load custom sounds or generate defaults."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sounds_dir = os.path.join(script_dir, 'assets', 'sounds')

        sound_types = ['move', 'capture', 'check', 'checkmate', 'castle', 'illegal', 'game_start']

        for sound_type in sound_types:
            # Try to load custom sound file
            for ext in ['.wav', '.ogg', '.mp3']:
                sound_path = os.path.join(sounds_dir, f'{sound_type}{ext}')
                if os.path.exists(sound_path):
                    try:
                        self.sounds[sound_type] = pygame.mixer.Sound(sound_path)
                        break
                    except:
                        pass

            # Generate default sound if not loaded
            if sound_type not in self.sounds:
                self.sounds[sound_type] = self._generate_sound(sound_type)

    def _generate_sound(self, sound_type: str) -> pygame.mixer.Sound:
        """Generate a sound programmatically."""
        sample_rate = 44100

        if sound_type == 'move':
            # Soft click - short sine wave with quick decay
            duration = 0.08
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            frequency = 600
            wave = np.sin(2 * np.pi * frequency * t)
            # Quick decay envelope
            envelope = np.exp(-t * 40)
            wave = wave * envelope * 0.3

        elif sound_type == 'capture':
            # Sharper snap - higher frequency, slightly longer
            duration = 0.12
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            frequency = 800
            wave = np.sin(2 * np.pi * frequency * t)
            # Add some harmonics for "snap" feel
            wave += 0.3 * np.sin(2 * np.pi * frequency * 2 * t)
            envelope = np.exp(-t * 30)
            wave = wave * envelope * 0.4

        elif sound_type == 'check':
            # Alert tone - two quick beeps
            duration = 0.25
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            frequency = 880
            wave = np.sin(2 * np.pi * frequency * t)
            # Two beep envelope
            envelope = np.zeros_like(t)
            envelope[t < 0.08] = 1
            envelope[(t > 0.12) & (t < 0.20)] = 1
            envelope = envelope * np.exp(-((t % 0.12) * 15))
            wave = wave * envelope * 0.35

        elif sound_type == 'checkmate':
            # Victory fanfare - ascending notes
            duration = 0.6
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            wave = np.zeros(samples)
            notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
            note_duration = duration / len(notes)
            for i, freq in enumerate(notes):
                start = int(i * note_duration * sample_rate)
                end = int((i + 1) * note_duration * sample_rate)
                note_t = t[start:end] - t[start]
                note_wave = np.sin(2 * np.pi * freq * note_t)
                envelope = np.exp(-note_t * 5)
                wave[start:end] = note_wave * envelope
            wave = wave * 0.3

        elif sound_type == 'castle':
            # Sliding sound - descending sweep
            duration = 0.2
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            # Frequency sweep from 800 to 400 Hz
            frequency = 800 - 400 * (t / duration)
            phase = 2 * np.pi * np.cumsum(frequency) / sample_rate
            wave = np.sin(phase)
            envelope = np.exp(-t * 10)
            wave = wave * envelope * 0.25

        elif sound_type == 'illegal':
            # Error buzz - low frequency buzz
            duration = 0.15
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            frequency = 200
            wave = np.sign(np.sin(2 * np.pi * frequency * t))  # Square wave
            envelope = np.exp(-t * 15)
            wave = wave * envelope * 0.2

        elif sound_type == 'game_start':
            # Pleasant ding
            duration = 0.3
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            frequency = 1047  # C6
            wave = np.sin(2 * np.pi * frequency * t)
            wave += 0.5 * np.sin(2 * np.pi * frequency * 2 * t)  # Harmonic
            envelope = np.exp(-t * 8)
            wave = wave * envelope * 0.25

        else:
            # Default beep
            duration = 0.1
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, False)
            wave = np.sin(2 * np.pi * 440 * t) * 0.3

        # Convert to 16-bit signed integers
        wave = np.clip(wave, -1, 1)
        audio = (wave * 32767).astype(np.int16)

        # Make stereo
        stereo = np.column_stack((audio, audio))

        return pygame.mixer.Sound(buffer=stereo.tobytes())

    def play(self, sound_type: str):
        """Play a sound effect."""
        if self.muted:
            return

        if sound_type in self.sounds:
            self.sounds[sound_type].play()

    def toggle_mute(self) -> bool:
        """Toggle mute state. Returns new mute state."""
        self.muted = not self.muted
        return self.muted

    def set_mute(self, muted: bool):
        """Set mute state."""
        self.muted = muted

    def is_muted(self) -> bool:
        """Check if sounds are muted."""
        return self.muted
