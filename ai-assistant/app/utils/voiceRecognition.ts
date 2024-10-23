// Use webkitSpeechRecognition for voice recognition

// Define the setupVoiceRecognition function to set up the voice recognition
export function setupVoiceRecognition(
  onInterimTranscript: (transcript: string) => void,
  onFinalTranscript: (transcript: string) => void
) {
  let recognition: any = null;
  let isRecognitionActive = false;
  let isListening = false;

  // Check if webkitSpeechRecognition is supported in the browser
  if ('webkitSpeechRecognition' in window) {
    recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US'; 

    recognition.onstart = () => {
      console.log('Voice recognition started');
      isRecognitionActive = true;
    };

    recognition.onerror = (event: any) => {
      console.error('Voice recognition error:', event.error);
      if (event.error === 'no-speech') {
        recognition.stop();
        isRecognitionActive = false;
        isListening = false;
      }
    };

    recognition.onend = () => {
      console.log('Voice recognition ended');
      isRecognitionActive = false;
      
      if (isListening) {
        setTimeout(() => {
          if (!isRecognitionActive && isListening) {
            try {
              recognition.start();
            } catch (error) {
              console.error('Error restarting recognition:', error);
            }
          }
        }, 100);
      }
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (interimTranscript) {
        console.log('Interim transcript:', interimTranscript);
        onInterimTranscript(interimTranscript);
      }
      
      if (finalTranscript) {
        console.log('Final transcript:', finalTranscript);
        onFinalTranscript(finalTranscript);
      }
    };
  } else {
    console.warn('Web Speech API is not supported in this browser');
  }

  return {
    start: () => {
      if (recognition && !isRecognitionActive) {
        try {
          recognition.start();
          isListening = true;
          console.log('Starting voice recognition...');
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
          console.log('Stopping voice recognition...');
        } catch (error) {
          console.error('Error stopping voice recognition:', error);
        }
      }
    },
    isListening: () => isListening
  };
}
