Voice Transcription
===================

The Clarity Opsbot now supports automatic transcription of Telegram voice notes.

Prerequisites
-------------
- `google-generativeai` package (bundled via project dependencies)
- Google Gemini API key with access to the specified audio model

Environment Variables
---------------------
- `GEMINI_API_KEY` – required. Enables calls to the Gemini API.
- `GEMINI_TRANSCRIPTION_MODEL` – optional. Defaults to the Gemini text model name or `gemini-flash-latest` if unset.

Runtime Behaviour
-----------------
- When a voice note arrives in a group chat, the bot downloads the audio and submits it to Gemini for transcription.
- The transcript is replied inline to the originating message and forwarded into the analysis pipeline (and map feature, if enabled) as a voice observation.
- If transcription is unavailable (missing key or package), the bot politely informs the user and logs a warning.

Operational Notes
-----------------
- Temporary audio files are stored on disk during upload and removed afterwards.
- Uploaded audio artefacts are deleted from Gemini once the transcription completes.
- Confidence handling for map integration mirrors text observations; combined voice+location updates retain their original source type.
