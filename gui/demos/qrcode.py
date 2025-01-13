# qrcode_test.py Test/demo of QRCodeWidget for nano-gui

# Inicialize o hardware e o framebuf antes de importar módulos.
from color_setup import ssd  # Configuração do display
from gui.core.nanogui import refresh
from gui.core.writer import CWriter
from gui.core.colors import *
import gui.fonts.arial10 as arial10  # Substitua pela fonte disponível
from gui.core.widgets import QRCodeWidget
import asyncio

# Argumentos comuns
qrcode_args = {
    "version": 6,
    "scale": 3,
    "fgcolor": BLUE,
    "bdcolor": RED,
    "bgcolor": WHITE,  # Garantir fundo branco
}

async def demo_qr(wri):
    # Inicializa o widget QRCode
    qr = QRCodeWidget(wri, 10, 10, **qrcode_args)  # Row=10, Col=10
    qr.value("https://example.com")  # Texto ou URL para o QR Code
    qr.show()
    refresh(ssd)  # Atualiza o display

    await asyncio.sleep(3)  # Exibe o QR Code por 3 segundos

    # Testa outro QR Code
    qr.value("Hello, NanoGUI!")
    qr.show()
    refresh(ssd)  # Atualiza o display novamente
    await asyncio.sleep(3)

async def main(wri):
    await demo_qr(wri)

def test():
    refresh(ssd, True)  # Inicializa e limpa o display
    CWriter.set_textpos(ssd, 0, 0)  # Garante posição inicial
    wri = CWriter(ssd, arial10, WHITE, BLACK, verbose=False)
    wri.set_clip(True, True, False)
    asyncio.run(main(wri))

test()

