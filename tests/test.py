import unittest

from scripts.media_utils import extract_title_and_artist

class TestExtractTitleAndArtist(unittest.TestCase):

    def test_extract_title_and_artist(self):
        test_cases = [
            ("快晴 / Orangestar full covered by 桃鈴ねね", ("快晴", "Orangestar full covered by 桃鈴ねね")),
            ("choose♡happiness - Mitsukiyo feat. ななひら", ("choose♡happiness", "Mitsukiyo feat. ななひら")),
            ("adrenaline!!! / TrySail (covered by しぐれうい＆大空スバル)", ("adrenaline!!!", "TrySail (covered by しぐれうい＆大空スバル)")),
            ("「リトライ☆ランデヴー」を歌ってみた＊ななひら", ("リトライ☆ランデヴー", "＊ななひら")),
            ("【歌ってみた】流星のパルス / 花雲くゆり、さけこ。、ななひら、浅木ゆめみ", ("流星のパルス", "花雲くゆり、さけこ。、ななひら、浅木ゆめみ")),
            ("【オリジナル曲】ぷ・れ・あ・で・す！【ホロライブ/大空スバル】", ("ぷ・れ・あ・で・す！", "")),
            ("魔法少女とチョコレゐト ♡ 星川サラ＆紫咲シオン", ("魔法少女とチョコレゐト ♡ 星川サラ＆紫咲シオン", "")),
            ("ねぇねぇねぇ。／Covered by紫咲シオン＆湊あくあ【歌ってみた】", ("ねぇねぇねぇ。", "Covered by紫咲シオン＆湊あくあ")),
            ("メンヘラじゃないもん！ /Cover 湊あくあ/紫咲シオン【ホロライブ】", ("メンヘラじゃないもん！", "Cover 湊あくあ/紫咲シオン")),
            ("KONKON Beats/白上フブキ(Original)", ("KONKON Beats", "白上フブキ(Original)")),
            ("かめりあ feat. ななひら - クリスマスなんて興味ないけど", ("クリスマスなんて興味ないけど", "かめりあ feat. ななひら")),
            ("[Fan M/V] おちゃめ機能 (全員参加)", ("おちゃめ機能 (全員参加)", "")),
        ]

        for title, result in test_cases:
            self.assertEqual(extract_title_and_artist(title), result)
