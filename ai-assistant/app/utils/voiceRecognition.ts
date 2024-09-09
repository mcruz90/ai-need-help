export function setupVoiceRecognition(
  onInterimTranscript: (transcript: string) => void,
  onFinalTranscript: (transcript: string) => void
) {
  let recognition: any = null;
  let isRecognitionActive = false;

  if ('webkitSpeechRecognition' in window) {
    recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onstart = () => {
      console.log('Voice recognition started');
      isRecognitionActive = true;
    };

    recognition.onerror = (event: any) => {
      console.error('Voice recognition error:', event.error);
      if (event.error === 'no-speech') {
        // Instead of restarting immediately, we'll stop and let the onend handler restart
        recognition.stop();
      }
    };

    recognition.onend = () => {
      console.log('Voice recognition ended');
      isRecognitionActive = false;
      // Only restart if we're supposed to be listening
      if (isListening) {
        setTimeout(() => {
          if (!isRecognitionActive && isListening) {
            recognition.start();
          }
        }, 100);
      }
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      if (interimTranscript) {
        onInterimTranscript(interimTranscript);
      }
      
      if (finalTranscript) {
        onFinalTranscript(finalTranscript);
      }
    };
  } else {
    console.warn('Web Speech API is not supported in this browser');
  }

  let isListening = false;

  return {
    start: () => {
      if (recognition && !isRecognitionActive) {
        try {
          recognition.start();
          isListening = true;
        } catch (error) {
          console.error('Error starting voice recognition:', error);
        }
      } else {
        console.warn('Recognition not available or already active');
      }
    },
    stop: () => {
      if (recognition) {
        try {
          recognition.stop();
          isListening = false;
        } catch (error) {
          console.error('Error stopping voice recognition:', error);
        }
      }
    },
  };
}