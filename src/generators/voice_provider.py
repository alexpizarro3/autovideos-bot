import asyncio
import logging
import edge_tts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceProvider:
    def __init__(self, voice="en-US-ChristopherNeural"):
        """
        Initialize the Voice Provider.
        Voices: en-US-AriaNeural, en-US-GuyNeural, en-US-JennyNeural, etc.
        """
        self.voice = voice

    async def _generate_audio_async(self, text: str, output_file: str) -> str:
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)
        return output_file

    def generate_voice(self, text: str, output_file: str) -> str:
        """
        Generates TTS audio for the given text and saves it to output_file.
        Returns the path to the output file.
        """
        try:
            logger.info(f"Generating voice for text: '{text[:30]}...' -> {output_file}")
            asyncio.run(self._generate_audio_async(text, output_file))
            return output_file
        except Exception as e:
            logger.error(f"Error generating voice: {e}")
            raise e

if __name__ == "__main__":
    vp = VoiceProvider()
    vp.generate_voice("Hello, this is a test of the daily video bot voice system.", "test_voice.mp3")
