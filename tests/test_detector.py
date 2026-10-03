from engines.change_detection.detector import detect_price_change

def test_price_change():
    c=detect_price_change(100,90)
    assert c["type"]=="PRICE_CHANGED"
    assert c["magnitude"]==10
