// recorder-processor.js
class RecorderProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const input = inputs[0];

        // Mono: use channel 0
        if (input && input[0]) {
            // Send Float32Array back to main thread
            this.port.postMessage(input[0]);
        }

        // Returning true keeps the processor alive
        return true;
    }
}

registerProcessor('recorder-processor', RecorderProcessor);
