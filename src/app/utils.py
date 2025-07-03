def to_pgvector_str(vec):
    return '[' + ','.join(str(float(x)) for x in vec) + ']' 