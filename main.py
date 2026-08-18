import re
import threading
from io import BytesIO
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

try:
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET])
except Exception:
    pass


APP_DIR = os.path.dirname(os.path.abspath(__file__))
SHARE_IMAGE = os.path.join(APP_DIR, "produto_divulgacao.jpg")


def clean_text(value):
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def meta_content(soup, *names):
    for name in names:
        tag = soup.find("meta", attrs={"property": name})
        if tag and tag.get("content"):
            return clean_text(tag["content"])
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return clean_text(tag["content"])
    return ""


def extract_price(soup, text):
    # OpenGraph / meta
    for key in [
        "product:price:amount", "product:price",
        "og:price:amount", "price"
    ]:
        value = meta_content(soup, key)
        if value:
            return value

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text()
        if not raw:
            continue
        matches = re.findall(
            r'"price"\s*:\s*"?(?:R\$\s*)?([0-9][0-9\.,]*)',
            raw, flags=re.I
        )
        if matches:
            return matches[0]

    # Common Brazilian price formats
    patterns = [
        r'R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})',
        r'R\$\s*\d+(?:,\d{2})',
        r'\b\d{1,3}(?:\.\d{3})*,\d{2}\b'
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.I)
        if m:
            return m.group(0).strip()

    return ""


def extract_product(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Android 13; Mobile) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36"
        )
    }

    response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = (
        meta_content(soup, "og:title", "twitter:title")
        or clean_text(soup.title.get_text() if soup.title else "")
    )

    description = meta_content(
        soup, "og:description", "twitter:description", "description"
    )

    image_url = meta_content(soup, "og:image", "twitter:image")
    if image_url:
        image_url = urljoin(response.url, image_url)

    price = extract_price(soup, soup.get_text(" ", strip=True))

    if not title:
        raise ValueError("Não consegui encontrar o nome do produto nessa página.")

    return {
        "name": title,
        "price": price or "Preço não encontrado",
        "link": response.url,
        "image_url": image_url,
        "description": description,
    }


def download_image(url):
    if not url:
        return None
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


def fit_font(size, bold=False):
    candidates = []
    if bold:
        candidates += [
            "/system/fonts/Roboto-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        ]
    else:
        candidates += [
            "/system/fonts/Roboto-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_share_card(data, product_image):
    W, H = 1080, 1350
    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)

    # Header
    draw.rectangle((0, 0, W, 150), fill=(20, 20, 20))
    title_font = fit_font(48, True)
    small_font = fit_font(32, False)
    price_font = fit_font(62, True)

    draw.text((50, 48), "OFERTA", fill="white", font=title_font)

    # Product image area
    box = (50, 190, 1030, 820)
    if product_image:
        img = product_image.copy()
        img.thumbnail((box[2] - box[0], box[3] - box[1]))
        x = box[0] + ((box[2] - box[0]) - img.width) // 2
        y = box[1] + ((box[3] - box[1]) - img.height) // 2
        canvas.paste(img, (x, y))
    else:
        draw.rectangle(box, outline=(200, 200, 200), width=3)
        draw.text((300, 470), "Imagem não encontrada", fill=(80, 80, 80), font=small_font)

    # Text
    name_lines = wrap_text(draw, data["name"], title_font, 980)
    y = 870
    for line in name_lines[:3]:
        draw.text((50, y), line, fill=(20, 20, 20), font=title_font)
        y += 62

    draw.text((50, y + 20), data["price"], fill=(190, 30, 30), font=price_font)
    draw.text((50, y + 105), "Clique no link para ver a oferta", fill=(70, 70, 70), font=small_font)

    # Link shortened visually
    link_lines = wrap_text(draw, data["link"], small_font, 980)
    ly = y + 165
    for line in link_lines[:3]:
        draw.text((50, ly), line, fill=(40, 80, 150), font=small_font)
        ly += 42

    canvas.save(SHARE_IMAGE, quality=92)
    return SHARE_IMAGE


def share_to_whatsapp(image_path, text):
    try:
        from jnius import autoclass
        from android.runnable import run_on_ui_thread

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        String = autoclass("java.lang.String")
        Uri = autoclass("android.net.Uri")

        @run_on_ui_thread
        def _share():
            activity = PythonActivity.mActivity
            intent = Intent(Intent.ACTION_SEND)
            intent.setType("image/jpeg")
            intent.putExtra(Intent.EXTRA_TEXT, String(text))
            # A FileProvider URI would be required for the image on newer Android versions.
            # We use Android's file URI fallback only when supported.
            try:
                intent.putExtra(Intent.EXTRA_STREAM, Uri.parse("file://" + image_path))
            except Exception:
                pass
            chooser = Intent.createChooser(intent, String("Compartilhar oferta"))
            activity.startActivity(chooser)

        _share()
        return True, ""
    except Exception as e:
        return False, str(e)


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)

        self.add_widget(Label(
            text="Divulgador de Produtos",
            size_hint_y=None, height=dp(55),
            font_size=dp(24), bold=True
        ))

        self.url_input = TextInput(
            hint_text="Cole aqui o link do produto",
            multiline=False,
            size_hint_y=None, height=dp(52)
        )
        self.add_widget(self.url_input)

        self.fetch_button = Button(
            text="BUSCAR PRODUTO",
            size_hint_y=None, height=dp(52)
        )
        self.fetch_button.bind(on_release=self.start_fetch)
        self.add_widget(self.fetch_button)

        scroll = ScrollView()
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter("height"))

        self.preview = KivyImage(
            source="",
            size_hint_y=None,
            height=dp(330),
            allow_stretch=True
        )
        content.add_widget(self.preview)

        self.name_label = Label(
            text="Nome: -",
            size_hint_y=None, height=dp(75),
            text_size=(dp(340), None),
            halign="left", valign="middle"
        )
        content.add_widget(self.name_label)

        self.price_label = Label(
            text="Valor: -",
            size_hint_y=None, height=dp(55),
            text_size=(dp(340), None),
            halign="left", valign="middle"
        )
        content.add_widget(self.price_label)

        self.link_label = Label(
            text="Link: -",
            size_hint_y=None, height=dp(90),
            text_size=(dp(340), None),
            halign="left", valign="middle"
        )
        content.add_widget(self.link_label)

        self.status = Label(
            text="Cole um link e toque em BUSCAR PRODUTO.",
            size_hint_y=None, height=dp(70),
            text_size=(dp(340), None),
            halign="center", valign="middle"
        )
        content.add_widget(self.status)

        self.share_button = Button(
            text="COMPARTILHAR NO WHATSAPP",
            size_hint_y=None, height=dp(58),
            disabled=True
        )
        self.share_button.bind(on_release=self.share)
        content.add_widget(self.share_button)

        scroll.add_widget(content)
        self.add_widget(scroll)

        self.data = None

    def set_status(self, text):
        self.status.text = text

    def start_fetch(self, *_):
        url = self.url_input.text.strip()
        if not url.startswith(("http://", "https://")):
            self.set_status("Cole um link completo começando com http:// ou https://")
            return

        self.fetch_button.disabled = True
        self.share_button.disabled = True
        self.set_status("Buscando informações...")
        threading.Thread(target=self.fetch_worker, args=(url,), daemon=True).start()

    def fetch_worker(self, url):
        try:
            data = extract_product(url)
            product_img = download_image(data["image_url"])
            card = make_share_card(data, product_img)

            # Kivy can load the generated local file.
            Clock.schedule_once(lambda dt: self.update_ui(data, card), 0)
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self.fetch_error(str(e)), 0
            )

    def update_ui(self, data, card):
        self.data = data
        self.fetch_button.disabled = False
        self.share_button.disabled = False
        self.name_label.text = "Nome: " + data["name"]
        self.price_label.text = "Valor: " + data["price"]
        self.link_label.text = "Link: " + data["link"]
        self.preview.source = card
        self.preview.reload()
        self.set_status("Produto encontrado! Você já pode compartilhar.")

    def fetch_error(self, message):
        self.fetch_button.disabled = False
        self.share_button.disabled = True
        self.set_status("Erro: " + message)

    def share(self, *_):
        if not self.data:
            return
        text = (
            f"{self.data['name']}\n\n"
            f"💰 {self.data['price']}\n\n"
            f"🔗 {self.data['link']}"
        )
        ok, error = share_to_whatsapp(SHARE_IMAGE, text)
        if not ok:
            self.set_status(
                "O compartilhamento automático não funcionou neste aparelho. "
                "Use o botão de compartilhar do Android. Detalhe: " + error
            )


class ProductApp(App):
    def build(self):
        Window.softinput_mode = "below_target"
        return MainScreen()


if __name__ == "__main__":
    ProductApp().run()
