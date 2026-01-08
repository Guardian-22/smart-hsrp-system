"""
Note:
- For single-frame, standard traffic monitoring, ThreadPoolExecutor is sufficient.
- In the future, for processing multiple frames or high-throughput streams:
    1. Use ProcessPoolExecutor to bypass Python GIL for CPU-heavy tasks.
    2. Use Batch Inference (e.g., model([img1, img2, ...])) to fully utilize GPU resources.
- This ensures scalability for multiple cameras or high-traffic scenarios.
"""


from concurrent.futures import ThreadPoolExecutor

def run_parallel(functions: list, args_list: list):
    """
    Executes multiple model inferences (Helmet, Plate, etc.) simultaneously.
    
    Args:
        functions (list): List of class methods (e.g., [helmet.predict, plate.predict])
        args_list (list): List of argument tuples (e.g., [(img,), (img,)])

    Returns:
        list: Results in the same order as the input functions.
    """
    # Using max_workers=len(functions) ensures no task waits in a queue
    with ThreadPoolExecutor(max_workers=len(functions)) as executor:
        # submit() starts the thread immediately
        futures = [
            executor.submit(fn, *args) 
            for fn, args in zip(functions, args_list)
        ]
        
        # future.result() waits for completion and returns the detector's dict/tuple
        return [future.result() for future in futures]
