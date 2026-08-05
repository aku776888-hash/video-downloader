const express = require('express');
const { exec } = require('child_process');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.get('/', (req, res) => {
    res.send(`
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VIDEO DOWNLOADER</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 40px 20px; margin: 0; }
            .container { background: #1e293b; max-width: 500px; margin: auto; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
            h2 { color: #38bdf8; margin-bottom: 10px; }
            p { color: #94a3b8; font-size: 14px; margin-bottom: 25px; }
            input { width: 100%; padding: 14px; margin-bottom: 15px; border: 1px solid #334155; background: #0f172a; color: white; border-radius: 8px; box-sizing: border-box; font-size: 14px; outline: none; }
            button { width: 100%; padding: 14px; background: #0284c7; color: white; border: none; font-weight: bold; border-radius: 8px; cursor: pointer; font-size: 16px; transition: background 0.2s; }
            button:hover { background: #0369a1; }
            
            .loading { display: none; margin-top: 20px; color: #38bdf8; font-size: 15px; font-weight: bold; }
            .spinner { display: inline-block; width: 18px; height: 18px; border: 3px solid rgba(56, 189, 248, 0.3); border-radius: 50%; border-top-color: #38bdf8; animation: spin 0.8s linear infinite; margin-right: 8px; vertical-align: middle; }
            @keyframes spin { to { transform: rotate(360deg); } }

            .info { margin-top: 25px; font-size: 13px; color: #64748b; }
            .platforms { font-size: 12px; color: #38bdf8; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🚀 VIDEO DOWNLOADER</h2>
            <p>Download Video YouTube, TikTok & IG Full HD</p>
            <div class="platforms">YouTube • TikTok • Instagram</div>
            
            <form action="/download" method="GET" id="downloadForm">
                <input type="url" name="url" id="urlInput" placeholder="Tempel link YouTube, TikTok, atau IG..." required />
                <button type="submit" id="submitBtn">Download Sekarang</button>
            </form>

            <div class="loading" id="loadingDiv">
                <span class="spinner"></span> Sedang memproses dan menggabungkan video & audio...
            </div>

            <div class="info">Didukung oleh yt-dlp & FFmpeg Audio Merger</div>
        </div>

        <script>
            const form = document.getElementById('downloadForm');
            const loadingDiv = document.getElementById('loadingDiv');
            const submitBtn = document.getElementById('submitBtn');

            form.addEventListener('submit', (e) => {
                const urlInput = document.getElementById('urlInput').value.trim();
                if (urlInput) {
                    submitBtn.style.display = 'none';
                    loadingDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    `);
});

app.get('/download', (req, res) => {
    const videoURL = req.query.url;
    if (!videoURL) return res.redirect('/');

    const outputFilename = `video_${Date.now()}.mp4`;
    const command = `yt-dlp -f "bestvideo[height<=1080]+bestaudio/best[height<=1080] / best" --merge-output-format mp4 -o "${outputFilename}" "${videoURL}"`;

    console.log('Sedang memproses dan menggabungkan video & audio...');

    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(error);
            return res.send(`
                <script>
                    alert('Gagal memproses video! Pastikan link aktif, publik, dan didukung.');
                    window.location.href = '/';
                </script>
            `);
        }

        res.download(outputFilename, 'video_hd.mp4', (err) => {
            if (err) console.error(err);
            exec(`rm "${outputFilename}"`);
        });
    });
});

app.listen(process.env.PORT || 5000, () => {
    console.log('Server aktif');
});
