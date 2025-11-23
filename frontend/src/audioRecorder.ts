/**
 * Browser-based audio recorder that captures microphone audio
 * and streams it to the backend WebSocket.
 */

export class AudioRecorder {
    private audioContext: AudioContext | null = null;
    private mediaStream: MediaStream | null = null;
    private processor: AudioWorkletNode | null = null;
    private source: MediaStreamAudioSourceNode | null = null;
    private sendAudioChunk: ((data: ArrayBuffer) => void) | null = null;

    async start(onAudioChunk: (data: ArrayBuffer) => void): Promise<void> {
        this.sendAudioChunk = onAudioChunk;

        try {
            // Request microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Create audio context (16kHz sample rate to match backend expectations)
            this.audioContext = new AudioContext({ sampleRate: 16000 });
            this.source = this.audioContext.createMediaStreamSource(this.mediaStream);

            // Load the audio worklet processor module
            // Adjust the path so it matches where recorder-processor.js is served
            await this.audioContext.audioWorklet.addModule('/recorder-processor.js');

            // Create the AudioWorkletNode using the registered processor name
            this.processor = new AudioWorkletNode(this.audioContext, 'recorder-processor');

            // Receive Float32 samples from the worklet and convert to Int16 PCM
            this.processor.port.onmessage = (event: MessageEvent<Float32Array>) => {
                const inputData = event.data;
                if (!this.sendAudioChunk) return;

                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    const sample = Math.max(-1, Math.min(1, inputData[i]));
                    pcmData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
                }

                this.sendAudioChunk(pcmData.buffer);
            };

            // Connect nodes (you can skip connecting to destination if you don't want playback)
            this.source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);

            console.log('[Audio] Recording started (AudioWorklet)');
        } catch (error) {
            console.error('[Audio] Failed to start recording:', error);
            throw error;
        }
    }

    stop(): void {
        if (this.processor) {
            try {
                this.processor.disconnect();
            } catch { }
            this.processor = null;
        }

        if (this.source) {
            try {
                this.source.disconnect();
            } catch { }
            this.source = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.sendAudioChunk = null;
        console.log('[Audio] Recording stopped');
    }
}
