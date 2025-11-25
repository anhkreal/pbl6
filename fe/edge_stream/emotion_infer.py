import random
NEGATIVE = ['sad','angry','fear','disgust']
POSITIVE = ['happy','surprise']
NEUTRAL = ['neutral']

def infer_emotion(frame):
    # placeholder random inference
    label = random.choice(NEGATIVE + POSITIVE + NEUTRAL)
    if label in NEGATIVE:
        etype = 'negative'
    elif label in POSITIVE:
        etype = 'positive'
    else:
        etype = 'neutral'
    score = round(random.random(), 3)
    return label, etype, score
