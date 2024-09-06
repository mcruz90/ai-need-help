export function setupVoiceRecognition(
  onInterimTranscript: (transcript: string) => void,
  onFinalTranscript: (transcript: string) => void
) {
  let recognition: any = null;

  if ('webkitSpeechRecognition' in window) {
    recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

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
  }

  return {
    start: () => {
      if (recognition) {
        recognition.start();
      }
    },
    stop: () => {
      if (recognition) {
        recognition.stop();
      }
    },
  };
}