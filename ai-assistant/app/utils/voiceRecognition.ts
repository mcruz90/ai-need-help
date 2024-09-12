// Use webkitSpeechRecognition for voice recognition
// Define the setupVoiceRecognition function to set up the voice recognition
export function setupVoiceRecognition(
  onInterimTranscript: (transcript: string) => void,
  onFinalTranscript: (transcript: string) => void
) {
  let recognition: any = null;
  let isRecognitionActive = false;

  // Check if webkitSpeechRecognition is supported in the browser
  if ('webkitSpeechRecognition' in window) {
    recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    // Define the onstart event handler to log when voice recognition starts
    recognition.onstart = () => {
      console.log('Voice recognition started');
      isRecognitionActive = true;
    };

    // Define the onerror event handler to log any errors that occur during voice recognition
    recognition.onerror = (event: any) => {
      console.error('Voice recognition error:', event.error);
      if (event.error === 'no-speech') {
        recognition.stop();
      }
    };

    // Define the onend event handler to log when voice recognition ends
    recognition.onend = () => {
      console.log('Voice recognition ended');
      isRecognitionActive = false;
      
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