import speech_recognition as sr
from openai.resources.chat.completions import ChatCompletion

from transcript import parse_openai_response
# Initialize recognizer
recognizer: sr.Recognizer = sr.Recognizer()

# Load the audio file
# Replace with your audio file path
audio_file = "/Users/dipesh/Downloads/output.wav"
with sr.AudioFile(audio_file) as source:
    audio = recognizer.record(source)  # Read the audio file

# Perform transcription
try:
    transcription: str = recognizer.recognize_google(audio)
    print("Transcription:")
    print(transcription)
except sr.UnknownValueError:
    print("Speech recognition could not understand the audio.")
except sr.RequestError as e:
    print(f"Could not request results; {e}")


TEST_URL = "https://www.youtube.com/watch?v=qCbfTN-caFI"


out = [{'topic': 'Exchange of Political Insults', 'start': '0.0', 'end': '15.6'}, {'topic': 'Politics as a Game', 'start': '17.94', 'end': '41.19'}, {'topic': 'Medical Marijuana', 'start': '41.19', 'end': '48.42'}, {'topic': 'Discussion on Jeffrey Epstein', 'start': '54.96', 'end': '57.72'}, {'topic': 'Interview Introduction', 'start': '63.33', 'end': '76.38'}, {'topic': 'Winning and Losing - Psychology', 'start': '84.63', 'end': '111.96'}, {'topic': 'Close Relationships with Sports Legends', 'start': '111.96', 'end': '155.94'}, {'topic': 'Different Mindsets of Champions', 'start': '155.94', 'end': '219.81'}, {'topic': 'Politics as a Dirty Game', 'start': '231.48', 'end': '290.16'}, {'topic': 'Business Success vs Politics', 'start': '328.35', 'end': '467.73'}, {'topic': 'Negotiating Peace in Ukraine', 'start': '471.37', 'end': '601.22'}, {'topic': 'Election Concerns and Voting', 'start': '672.45', 'end': '1083.78'}, {'topic': 'Interview on Immigration Policies', 'start': '1182.75', 'end': '1374.96'}, {'topic': 'Mass Deportations & Eisenhower Reference', 'start': '1378.32', 'end': '1444.02'}, {'topic': 'Project 2025 and Marijuana Legalization', 'start': '1444.02', 'end': '1559.28'}, {'topic': 'Psychedelics and Its Benefits', 'start': '1559.28', 'end': '1615.5'}, {'topic': 'Discussing the Joe Rogan Podcast', 'start': '1634.22', 'end': '1725.75'}, {'topic': 'Truth Social and Social Media Strategy', 'start': '1725.75', 'end': '1794.45'}, {'topic': 'Social Media Engagement and Night Thoughts', 'start': '1794.45', 'end': '1852.02'}, {'topic': 'Political Division and Ideal Leaders', 'start': '1852.02', 'end': '1904.52'}, {'topic': 'Accusations and Partisan Tactics', 'start': '1904.52', 'end': '2200.35'}, {'topic': 'Challenges of Political Campaigning', 'start': '2204.88', 'end': '2410.17'}, {'topic': 'Expressing National Pride and Immigrant Perspectives', 'start': '2882.07', 'end': '3112.44'}, {'topic': 'AI and the Future of Programming Jobs', 'start': '3362.1', 'end': '3628.64'}, {'topic': 'Personal Journey & Anxiety in Scientific Pursuit', 'start': '3628.64', 'end': '3845.46'}] 