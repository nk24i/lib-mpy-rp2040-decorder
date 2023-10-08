from src.lib.rp2040_decorder import Captcha


class TestCaptcha():
    def test_detect_error(self, mocker):
        captcha = Captcha()
        # mocker.patch.object(captcha, "packets", 0x033f370d) # expect return False with valid packets
        mocker.patch.object(captcha, "packets", b'\x03\x12\x63\x72') # expect return False with valid packets
        assert captcha.detect_error() == False