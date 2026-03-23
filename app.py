<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Outetts Generator</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <main class="page">
        <section class="card">
            <h1>Synthetic voices</h1>
            <p class="subtitle">Generate speech and watch live logs in the browser.</p>

            <form id="generate-form">
                <label for="model">Model</label>
                <select id="model" name="model" required>
                    {% if models %}
                        {% for model in models %}
                            <option value="{{ model }}">{{ model }}</option>
                        {% endfor %}
                    {% else %}
                        <option value="">No models found in ./models</option>
                    {% endif %}
                </select>

                <label for="prompt">Text to synthesize</label>
                <textarea id="prompt" name="prompt" rows="8" required></textarea>

                <label for="audio">Optional speaker file (.mp3 or .wav)</label>
                <input id="audio" name="audio" type="file" accept=".mp3,.wav,audio/mpeg,audio/wav">

                <div class="actions">
                    <button id="generate-btn" type="submit" {% if not models %}disabled{% endif %}>
                        Generate
                    </button>
                </div>
            </form>

            <div id="message" class="message hidden"></div>

            <h2>Console Output</h2>
            <pre id="log-box" class="log-box"></pre>

            <div id="audio-section" class="hidden">
                <h2>Output Preview</h2>
                <audio id="audio-player" controls></audio>
                <div class="downloads">
                    <a id="mp3-link" href="#" target="_blank">Open MP3</a>
                </div>
            </div>
        </section>
    </main>

    <script>
        const form = document.getElementById("generate-form");
        const generateBtn = document.getElementById("generate-btn");
        const logBox = document.getElementById("log-box");
        const messageBox = document.getElementById("message");
        const audioSection = document.getElementById("audio-section");
        const audioPlayer = document.getElementById("audio-player");
        const mp3Link = document.getElementById("mp3-link");

        let logSource = null;

        function setMessage(text, type) {
            messageBox.textContent = text;
            messageBox.className = `message ${type}`;
        }

        function clearMessage() {
            messageBox.textContent = "";
            messageBox.className = "message hidden";
        }

        function appendLog(line) {
            logBox.textContent += line + "\n";
            logBox.scrollTop = logBox.scrollHeight;
        }

        function resetUIForRun() {
            logBox.textContent = "";
            clearMessage();
            audioSection.classList.add("hidden");
            audioPlayer.removeAttribute("src");
            mp3Link.href = "#";
        }

        function startLogStream() {
            if (logSource) {
                logSource.close();
            }

            logSource = new EventSource("/logs");

            logSource.onmessage = (event) => {
                appendLog(event.data);
            };

            logSource.addEventListener("done", async () => {
                appendLog("[browser] Job finished.");
                logSource.close();
                logSource = null;
                await refreshStatus(true);
                generateBtn.disabled = false;
            });

            logSource.addEventListener("error", async (event) => {
                appendLog("[browser] Job failed: " + event.data);
                if (logSource) {
                    logSource.close();
                    logSource = null;
                }
                await refreshStatus(false);
                generateBtn.disabled = false;
            });
        }

        async function refreshStatus(expectSuccess = false) {
            const response = await fetch("/status");
            const status = await response.json();

            if (status.error) {
                setMessage(status.error, "error");
                return;
            }

            if (expectSuccess && status.output_mp3) {
                const filename = status.output_mp3.split("/").pop();
                const audioUrl = `/audio/${filename}?t=${Date.now()}`;
                audioPlayer.src = audioUrl;
                mp3Link.href = audioUrl;
                audioSection.classList.remove("hidden");
                setMessage(
                    `Generation completed successfully with model: ${status.selected_model}`,
                    "success"
                );
            }
        }

        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            resetUIForRun();
            generateBtn.disabled = true;
            setMessage("Generation started...", "info");

            const formData = new FormData(form);

            const response = await fetch("/generate", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (!response.ok || !result.ok) {
                setMessage(result.error || "Failed to start generation.", "error");
                generateBtn.disabled = false;
                return;
            }

            startLogStream();
        });
    </script>
</body>
</html>
