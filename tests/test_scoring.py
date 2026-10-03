from engines.change_detection.scoring import impact_score
def test_impact_score_is_bounded(): assert impact_score(100,100,100,100,100)==100
