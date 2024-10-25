import cProfile
import pstats
import io
from functools import wraps

def profile(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        result = await func(*args, **kwargs)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        with open(f'{func.__name__}_profile.txt', 'w') as f:
            f.write(s.getvalue())
        
        return result
    
    return wrapper
