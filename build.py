import os

# Read SVG
try:
    with open('map-full.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
        # Remove XML declaration if present
        if svg_content.startswith('<?xml'):
            svg_content = svg_content.split('?>', 1)[1].strip()
            
        # Move Okinawa to Bottom Right
        # We search for the specific group class string to be safe
        search_str = 'class="okinawa kyushu-okinawa prefecture" data-code="47"'
        
        if search_str in svg_content:
            # Move Okinawa
            old_transform = 'transform="translate(52.000000, 193.000000)"'
            new_transform = 'transform="translate(620.000000, 780.000000)"'
            
            if old_transform in svg_content:
                svg_content = svg_content.replace(old_transform, new_transform)
                print("Okinawa moved.")
                
                # Add Separator Line (Polyline) to the SVG
                # We insert it before the closing </svg> tag or inside the main group if possible.
                # The main group has a transform, so we should be careful.
                # Let's inspect the SVG structure from previous reads.
                # It has <g class="svg-map" ...> <g class="prefectures" ...>
                # We can append the line to the end of the content before </svg>.
                # Since we are just concatenating strings, we can append it after the map content.
                # However, the map content is inside 'svg_content'. 
                # Ideally we inject it into the 'svg-map' group or just overlay it.
                # The 'svg-map' group has a transform. If we add it outside, we use raw coordinates.
                # Let's add it typically at the end of the SVG content, usually before the last </g></g> or </svg>.
                # To be safe and simple, let's just replace the closing tag of the "prefectures" group if we can find it,
                # or just append to the end of the string before `</svg>`.
                
                # Coordinates for the separator line based on the user image:
                # Starts around (550, 600) goes down-right, then down? 
                # Or based on the image: L-shape or zig-zag.
                # Image shows: Starts left of Tohoku, goes down, then right to enclose Okinawa.
                # Let's approximate: 
                # (500, 500) -> (800, 800)? No, user image shows a specific "cutout" style.
                # Looking at image: It seems to be a line separating the main map from the bottom right inset.
                # The line goes from ~ (600, 800) up and left?
                # Let's draw a simple "corner" line for the inset.
                # Points: 580,1000 (bottom) -> 580,750 (up) -> 1000,550 (right-up diagonal)?
                # Let's try to match the "Japan map inset line" style.
                # Usually it's a line like: (550, 600) -> (700, 600) -> (800, 500)?
                # User image: straight line then diagonal up-right.
                # Let's try: <polyline points="550,1000 550,750 1000,300" ... /> (Approximate)
                # Actually, let's look at the uploaded image visually.
                # It's a line separating the ocean.
                # Let's add a polyline: <polyline points="600,1000 600,750 950,450" fill="none" stroke="#888" stroke-width="2"/>
                
                separator_line = '<polyline points="580,1000 580,750 1000,400" fill="none" stroke="#999" stroke-width="1" />'
                svg_content = svg_content.replace('</svg>', f'{separator_line}</svg>')
                
            else:
                print("Warning: Okinawa transform string not found exactly.")
        else:
             print("Warning: Okinawa group not found.")

except Exception as e:
    print(f"Error reading SVG: {e}")
    exit(1)

# HTML Structure
html_head = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>日本観光ガイド - JAPAN TOUR GUIDE</title>
    <style>
        :root {
            --primary-color: #A6CE39; /* Map Green */
            --hover-color: #C1E16C; /* Light Green */
            --border-color: #FFFFFF;
            --bg-color: #FFFFFF;
            --text-color: #333333;
            --accent-color: #FF6B6B;
        }
        
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 0;
            font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            overflow-x: hidden;
        }

        .app-container {
            display: flex;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
        }

        /* Map Section */
        .map-section {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            background-color: #f9f9f9;
            position: relative;
            overflow: auto;
        }

        .geolonia-svg-map {
            width: 100%;
            height: auto;
            max-height: 90vh;
            max-width: 900px;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));
        }

        /* SVG Styling */
        /* Apply to the group containing the path/polygon */
        .prefecture {
            fill: var(--primary-color);
            stroke: var(--border-color);
            stroke-width: 0.5px; /* Thinner border */
            cursor: pointer;
            transition: fill 0.2s ease;
            pointer-events: all;
        }

        .prefecture:hover {
            fill: var(--hover-color);
        }
        
        .prefecture.active {
            fill: #FFD700; /* Gold for selected */
        }
        
        /* Ensure child paths inherit interactions */
        .prefecture * {
            cursor: pointer;
            pointer-events: all;
        }

        /* Info Panel */
        .info-panel {
            width: 400px;
            background: white;
            box-shadow: -2px 0 10px rgba(0,0,0,0.1);
            padding: 30px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            z-index: 10;
        }

        .panel-header {
            border-bottom: 2px solid var(--primary-color);
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .prefecture-name {
            font-size: 2.5rem;
            margin: 0;
            color: var(--text-color);
        }

        .prefecture-en {
            color: #888;
            font-size: 1rem;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .info-card {
            background: #fff;
            border-radius: 12px;
            margin-bottom: 20px;
        }

        .info-item {
            margin-bottom: 25px;
        }

        .info-label {
            font-size: 0.9rem;
            color: var(--primary-color);
            font-weight: bold;
            display: block;
            margin-bottom: 5px;
        }

        .info-content {
            font-size: 1.1rem;
            line-height: 1.6;
        }

        .empty-state {
            text-align: center;
            color: #aaa;
            margin-top: 50%;
            transform: translateY(-50%);
        }

        /* Action Buttons */
        .action-buttons {
            margin-top: auto;
            padding-top: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .btn {
            display: block;
            width: 100%;
            padding: 12px;
            text-align: center;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            transition: background 0.2s, transform 0.1s;
            border: none;
            cursor: pointer;
        }

        .btn:active {
            transform: scale(0.98);
        }

        .btn-google {
            background-color: #4285F4;
            color: white;
        }
        .btn-google:hover { background-color: #357ae8; }

        .btn-maps {
            background-color: #34A853;
            color: white;
        }
        .btn-maps:hover { background-color: #2c8c45; }

        /* Responsive */
        @media (max-width: 768px) {
            .app-container {
                flex-direction: column;
                height: auto;
                min-height: 100vh;
            }

            .map-section {
                height: 60vh;
                padding: 10px;
            }

            .info-panel {
                width: 100%;
                height: auto;
                min-height: 40vh;
                box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="map-section">
"""

html_tail = """
        </div>
        <div class="info-panel" id="infoPanel">
            <div class="empty-state">
                <h2>日本地図へようこそ</h2>
                <p>地図上の都道府県をクリックして、<br>観光情報を見つけましょう！</p>
            </div>
        </div>
    </div>

    <script>
        // Data Store (Concierge Tone)
        const guideData = {
            1: {
                name: "北海道",
                en: "Hokkaido",
                spot: "四季彩の丘",
                food: "ジンギスカン・海鮮丼",
                hidden: "神の子池（清里町）",
                desc: "雄大な自然と美食の宝庫、北海道へようこそ。広大な大地で深呼吸し、四季折々の絶景をお楽しみください。"
            },
            13: {
                name: "東京都",
                en: "Tokyo",
                spot: "浅草寺・スカイツリー",
                food: "江戸前寿司・もんじゃ焼き",
                hidden: "等々力渓谷（世田谷区）",
                desc: "伝統と最先端が融合する大都市、東京。路地裏の情緒から摩天楼の輝きまで、刺激的な発見があなたを待っています。"
            },
            26: {
                name: "京都府",
                en: "Kyoto",
                spot: "清水寺・金閣寺",
                food: "京懐石・湯豆腐",
                hidden: "貴船神社（夜の灯篭）",
                desc: "千年の都、京都。歴史ある寺社仏閣の静寂と、四季の雅な移ろいに浸る、心安らぐ旅はいかがでしょうか。"
            },
            27: {
                name: "大阪府",
                en: "Osaka",
                spot: "道頓堀・USJ",
                food: "たこ焼き・お好み焼き",
                hidden: "箕面大滝",
                desc: "食い倒れの街、大阪。活気あふれる街並みと人情味、そして絶品グルメが、あなたの旅をエネルギッシュに彩ります。"
            },
            47: {
                name: "沖縄県",
                en: "Okinawa",
                spot: "美ら海水族館",
                food: "沖縄そば・ゴーヤチャンプルー",
                hidden: "果報バンタ（うるま市）",
                desc: "青い海と空、南国の楽園沖縄。ゆったりと流れる島時間の中で、心も体もリフレッシュする極上のひとときを。"
            }
        };

        const defaultData = {
            spot: "情報準備中...",
            food: "情報準備中...",
            hidden: "", // Removed from display
            desc: "現在、この都道府県の特別な観光プランを計画中です。詳細の公開まで今しばらくお待ちください。"
        };

        // DOM Elements
        const panel = document.getElementById('infoPanel');
        
        // Ensure SVG loaded before attaching
        const prefectures = document.querySelectorAll('.prefecture');

        // Event Listeners
        prefectures.forEach(pref => {
            // Click
            pref.addEventListener('click', (e) => {
                e.preventDefault(); 
                e.stopPropagation();

                const targetGroup = e.currentTarget; 
                if (!targetGroup) return;

                const codeStr = targetGroup.getAttribute('data-code');
                const code = parseInt(codeStr, 10);
                
                const titleEl = targetGroup.querySelector('title');
                
                let data = guideData[code];
                let name = "都道府県";
                let en = "";

                if (titleEl) {
                    const parts = titleEl.textContent.split('/');
                    name = parts[0].trim();
                    if (parts[1]) en = parts[1].trim();
                }

                if (!data) {
                    // Use Default Data
                    data = { ...defaultData, name: name, en: en };
                }

                updatePanel(data);
                
                // Active State
                prefectures.forEach(p => p.classList.remove('active'));
                targetGroup.classList.add('active');
            });
        });

        function updatePanel(data) {
            panel.innerHTML = `
                <div class="panel-header">
                    <h1 class="prefecture-name">${data.name}</h1>
                    <span class="prefecture-en">${data.en}</span>
                </div>
                
                <div class="info-item">
                    <p class="info-content">${data.desc}</p>
                </div>

                <div class="info-card">
                    <div style="padding:15px;">
                        <span class="info-label">【観光情報】</span>
                        <!-- Consolidated Info or Default Text -->
                        <div class="info-content">
                            ${(data.spot && data.spot !== defaultData.spot) ? `<strong>必見スポット:</strong> ${data.spot}<br>` : ''}
                            ${(data.food && data.food !== defaultData.food) ? `<strong>ローカルグルメ:</strong> ${data.food}<br>` : ''}
                            ${(!data.spot || data.spot === defaultData.spot) ? '地元の隠れた名所や絶品グルメなど、魅力的な観光情報を準備中です。' : ''}
                        </div>
                    </div>
                </div>

                <div class="action-buttons">
                    <a href="https://www.google.com/search?q=${encodeURIComponent(data.name)}+観光+おすすめ" target="_blank" class="btn btn-google">
                        Googleで観光情報を検索
                    </a>
                    <a href="https://www.google.com/maps/search/${encodeURIComponent(data.name)}+観光地" target="_blank" class="btn btn-maps">
                        Googleマップで確認
                    </a>
                </div>
            `;
        }
    </script>
</body>
</html>
"""

final_content = html_head + "\n" + svg_content + "\n" + html_tail

try:
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(final_content)
    print("Success: index.html created.")
except Exception as e:
    print(f"Error writing index.html: {e}")
    exit(1)
