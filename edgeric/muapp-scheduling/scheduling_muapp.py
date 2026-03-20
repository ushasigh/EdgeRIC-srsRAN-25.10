#!/usr/bin/env python3
"""
EdgeRIC Scheduling muApp - Redis-controlled scheduling algorithms

This muApp reads from Redis to decide which scheduling algorithm to use,
receives metrics from RAN via ZMQ, computes scheduling weights, and sends
them back to RAN with TTI for staleness checking.

Supported Algorithms:
- Fixed Weight: Static per-UE weight assignment
- Max CQI: Prioritize UE with best channel quality
- Max Weight: CQI * Backlog weighted scheduling
- Proportional Fair: Rate-proportional fairness
- Round Robin: Time-based round robin

Usage:
    # Start Redis first, then:
    python3 scheduling_muapp.py
    
    # Set algorithm via Redis:
    redis-cli SET scheduling_algorithm "Max CQI"

    Use This: sudo python3 scheduling_muapp.py --algorithm "Fixed Weight" --verbose
"""

import argparse
import os
import sys
import time
import numpy as np
import redis

from edgeric_messenger import (
    get_metrics_multi,
    get_tti_index,
    send_scheduling_weight,
    cleanup
)

# Global state
total_brate = []
avg_CQIs = []


def fixed_weights():
    """
    Fixed weight allocation - assign static weights per UE.
    
    Modify the weights assignment below to set your desired allocation.
    """
    global total_brate
    ue_data = get_metrics_multi()
    
    if not ue_data:
        return None
        
    numues = len(ue_data)
    weights = np.zeros(numues * 2)
    RNTIs = list(ue_data.keys())
    txb = [data['Tx_brate'] for data in ue_data.values()]
    brate = np.sum(txb)
    total_brate.append(brate)

    for i in range(numues):
        weights[i*2+0] = RNTIs[i]
        # Customize weights here:
        # Example: First UE gets 30%, second gets 70%, rest equal share
        if i == 0:
            weights[i*2+1] = 0.7
        elif i == 1:
            weights[i*2+1] = 0.3
        else:
            weights[i*2+1] = 1.0 / numues
    
    return weights


def algo1_maxCQI_multi():
    """
    Max CQI scheduling - prioritize UE with highest CQI.
    
    Gives 80% resources to best CQI UE, 10% to others.
    """
    global total_brate
    ue_data = get_metrics_multi()
    
    if not ue_data:
        return None
        
    numues = len(ue_data)
    weights = np.zeros(numues * 2)

    CQIs = [data['CQI'] for data in ue_data.values()]
    RNTIs = list(ue_data.keys())
    txb = [data['Tx_brate'] for data in ue_data.values()]
    brate = np.sum(txb)
    total_brate.append(brate)

    if min(CQIs) > 0:
        maxIndex = np.argmax(CQIs)
        new_weights = np.zeros(numues)
        
        high = 1 - ((numues - 1) * 0.1)
        low = 0.1
        
        for i in range(numues):
            if i == maxIndex:
                new_weights[i] = high
            else:
                new_weights[i] = low
            
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = new_weights[i]
        
        return weights
    else:
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = 1.0 / numues
        return weights


def algo2_maxWeight_multi():
    """
    Max Weight scheduling - CQI * Buffer weighted.
    
    Balances channel quality with queue buffer.
    Note: Uses ul_buffer to match original EdgeRIC implementation.
    """
    global total_brate
    ue_data = get_metrics_multi()
    
    if not ue_data:
        return None
        
    numues = len(ue_data)
    weights = np.zeros(numues * 2)
    
    CQIs = [data['CQI'] for data in ue_data.values()]
    RNTIs = list(ue_data.keys())
    BLs = [data['ul_buffer'] for data in ue_data.values()]  # Match original
    txb = [data['Tx_brate'] for data in ue_data.values()]
    brate = np.sum(txb)
    total_brate.append(brate)
    
    if min(CQIs) > 0:
        sum_CQI = np.sum(CQIs)
        sum_BL = np.sum(BLs)
        
        if sum_BL != 0:
            new_weights = (np.array(CQIs) / sum_CQI) * (np.array(BLs) / sum_BL)
        else:
            new_weights = np.array(CQIs) / sum_CQI
        
        # Normalize weights
        if np.sum(new_weights) > 0:
            new_weights = new_weights / np.sum(new_weights)
        else:
            new_weights = np.ones(numues) / numues
        
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = new_weights[i]
    else:
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = 1.0 / numues
    
    return weights


def algo3_propFair_multi(avg_CQIs):
    """
    Proportional Fair scheduling.
    
    Allocates based on instantaneous rate / average rate.
    """
    global total_brate
    ue_data = get_metrics_multi()
    
    if not ue_data:
        return None, avg_CQIs
        
    numues = len(ue_data)
    weights = np.zeros(numues * 2)
    
    CQIs = np.array([data['CQI'] for data in ue_data.values()])
    RNTIs = list(ue_data.keys())
    BLs = [data['ul_buffer'] for data in ue_data.values()]  # Match original
    txb = [data['Tx_brate'] for data in ue_data.values()]
    brate = np.sum(txb)
    total_brate.append(brate)

    # Ensure avg_CQIs has correct size
    if len(avg_CQIs) != numues:
        avg_CQIs = np.zeros(numues)

    if min(CQIs) > 0:
        gamma = 0.1  # Exponential moving average factor
        avg_CQIs = np.array(avg_CQIs)
        
        # Initialize averages
        for i in range(numues):
            if avg_CQIs[i] == 0:
                avg_CQIs[i] = CQIs[i]
        
        # Update exponential moving average
        avg_CQIs = avg_CQIs * (1 - gamma) + CQIs * gamma
        
        # Compute proportional fair weights
        temp_weights = CQIs / avg_CQIs
        new_weights = np.round(temp_weights / np.sum(temp_weights), 2)
        
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = new_weights[i]
    else:
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = 1.0 / numues

    return weights, avg_CQIs


def algo4_roundrobin_multi(rr_cnt):
    """
    Round Robin scheduling.
    
    Each UE gets priority in turn based on TTI.
    """
    global total_brate
    ue_data = get_metrics_multi()
    
    if not ue_data:
        return None
        
    numues = len(ue_data)
    weights = np.zeros(numues * 2)

    CQIs = [data['CQI'] for data in ue_data.values()]
    RNTIs = list(ue_data.keys())
    txb = [data['Tx_brate'] for data in ue_data.values()]
    brate = np.sum(txb)
    total_brate.append(brate)
    
    index = rr_cnt % numues

    if min(CQIs) > 0:
        new_weights = np.zeros(numues)
        
        high = 1 - ((numues - 1) * 0.1)
        low = 0.1
        
        for i in range(numues):
            if i == index:
                new_weights[i] = high
            else:
                new_weights[i] = low
            
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = new_weights[i]
        
        return weights
    else:
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = 1.0 / numues
        return weights


def eval_loop_weight(eval_episodes, idx_algo, verbose=False):
    """
    Main evaluation loop for weight-based scheduling.
    
    Args:
        eval_episodes: Number of TTIs to run
        idx_algo: Algorithm index (0-4)
        verbose: If True, print every weight message sent
    """
    global avg_CQIs
    avg_CQIs = np.zeros(10)  # Support up to 10 UEs
    rr_cnt = 0
    
    for i_episode in range(eval_episodes):
        weights = None
        value_algo = "Unknown"
        
        # Fixed Weights
        if idx_algo == 0:
            weights = fixed_weights()
            value_algo = "Fixed Weights"
        
        # Max CQI
        elif idx_algo == 1:
            weights = algo1_maxCQI_multi()
            value_algo = "MaxCQI"
        
        # Max Weight
        elif idx_algo == 2:
            weights = algo2_maxWeight_multi()
            value_algo = "MaxWeight"
        
        # Proportional Fair
        elif idx_algo == 3:
            weights, avg_CQIs = algo3_propFair_multi(avg_CQIs)
            value_algo = "Proportional Fairness"
        
        # Round Robin
        elif idx_algo == 4:
            weights = algo4_roundrobin_multi(rr_cnt)
            rr_cnt += 1
            value_algo = "Round Robin"
        
        # Send weights to RAN (verbose flag passed from caller)
        if weights is not None:
            send_scheduling_weight(weights, include_tti=True, verbose=verbose, tti_offset=0)
            
            # Log every 100 TTIs
            if i_episode % 100 == 0:
                tti = get_tti_index()
                print(f"[{value_algo}] TTI={tti}, weights sent for {len(weights)//2} UEs")


# Algorithm mapping
algorithm_mapping = {
    "Fixed Weight": 0,
    "Max CQI": 1,
    "Max Weight": 2,
    "Proportional Fair": 3,
    "Round Robin": 4,
}


def main():
    parser = argparse.ArgumentParser(description='EdgeRIC Scheduling muApp')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    parser.add_argument('--episodes', type=int, default=1000, 
                        help='Episodes per algorithm check')
    parser.add_argument('--algorithm', type=str, default=None,
                        help='Override Redis algorithm selection (Fixed Weight, Max CQI, Max Weight, Proportional Fair, Round Robin)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print every weight message sent to RAN')
    args = parser.parse_args()
    
    global total_brate
    
    # Connect to Redis
    redis_db = None
    if args.algorithm is None:
        try:
            redis_db = redis.Redis(
                host=args.redis_host, 
                port=args.redis_port, 
                db=0, 
                decode_responses=True
            )
            redis_db.ping()
            print(f"[EdgeRIC] Connected to Redis at {args.redis_host}:{args.redis_port}")
        except redis.exceptions.ConnectionError:
            print(f"[EdgeRIC] Warning: Cannot connect to Redis at {args.redis_host}:{args.redis_port}")
            print("[EdgeRIC] Using default algorithm: Proportional Fair")
            args.algorithm = "Proportional Fair"
    
    print("[EdgeRIC] Scheduling muApp started")
    print(f"[EdgeRIC] Available algorithms: {list(algorithm_mapping.keys())}")
    
    if args.algorithm:
        print(f"[EdgeRIC] Using fixed algorithm: {args.algorithm}")
    else:
        print("[EdgeRIC] Waiting for algorithm selection via Redis...")
        print("    Set with: redis-cli SET scheduling_algorithm \"Max CQI\"")
    
    try:
        while True:
            try:
                # Get algorithm selection
                if args.algorithm:
                    selected_algorithm = args.algorithm
                else:
                    selected_algorithm = redis_db.get('scheduling_algorithm')
                
                if selected_algorithm:
                    idx_algo = algorithm_mapping.get(selected_algorithm, None)
                    
                    if idx_algo is not None:
                        print(f"\n[EdgeRIC] Running: {selected_algorithm} (index={idx_algo})")
                        
                        eval_loop_weight(args.episodes, idx_algo, args.verbose)
                        
                        if total_brate:
                            throughput = np.mean(total_brate) * 8 / 1000  # kbps
                            print(f"[EdgeRIC] Avg throughput: {throughput:.2f} kbps")
                            total_brate.clear()
                    else:
                        print(f"[EdgeRIC] Unknown algorithm: {selected_algorithm}")
                        print(f"[EdgeRIC] Available: {list(algorithm_mapping.keys())}")
                        time.sleep(1)
                else:
                    print("[EdgeRIC] No algorithm selected in Redis. Waiting...")
                    time.sleep(1)
                    
            except redis.exceptions.RedisError as e:
                print(f"[EdgeRIC] Redis error: {e}")
                time.sleep(1)
            except Exception as e:
                print(f"[EdgeRIC] Error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n[EdgeRIC] Shutting down...")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
