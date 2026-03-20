#!/usr/bin/env python3
"""
EdgeRIC MCS muApp - Dynamic MCS Control

This muApp receives metrics from RAN, computes MCS values, and sends them back.
The RAN applies MCS overrides only if fresh (current_TTI - decision_TTI <= 2).

Algorithms:
- Fixed MCS: Set a specific MCS for all UEs
- Random MCS: Random MCS between 10-20 for each UE

Usage:
    python3 mcs_muapp.py --algorithm fixed --mcs 20
    python3 mcs_muapp.py --algorithm random
"""

import zmq
import sys
import os
import time
import random
import argparse
from typing import Dict, List, Tuple, Optional

# Add parent directory for protobuf imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import generated protobufs
try:
    import control_mcs_pb2
    import metrics_pb2
except ImportError:
    print("Error: Could not import protobufs. Generate them first:")
    print("  cd ../protobufs && protoc --python_out=.. *.proto")
    sys.exit(1)


class McsMessenger:
    """
    ZMQ messenger for MCS control.
    Receives metrics from RAN and sends MCS overrides.
    """
    
    def __init__(self,
                 mcs_ipc: str = "ipc:///tmp/control_mcs",
                 metrics_ipc: str = "ipc:///tmp/metrics_data"):
        self.context = zmq.Context()
        
        # Publisher for MCS control (with CONFLATE)
        self.mcs_socket = self.context.socket(zmq.PUB)
        self.mcs_socket.setsockopt(zmq.SNDHWM, 1)
        self.mcs_socket.setsockopt(zmq.CONFLATE, 1)
        self.mcs_socket.bind(mcs_ipc)
        
        # Subscriber for metrics (with CONFLATE)
        self.metrics_socket = self.context.socket(zmq.SUB)
        self.metrics_socket.setsockopt(zmq.CONFLATE, 1)
        self.metrics_socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.metrics_socket.connect(metrics_ipc)
        
        self.ran_index = 0
        self.current_tti = 0
        self.last_metrics = None
        
        # Give time for connection
        time.sleep(0.5)
        print(f"[MCS muApp] Connected to metrics: {metrics_ipc}")
        print(f"[MCS muApp] Bound to MCS control: {mcs_ipc}")
    
    def get_metrics(self) -> Optional[Dict[int, dict]]:
        """
        Get metrics for all UEs.
        
        Returns:
            Dictionary mapping RNTI -> metrics dict, or None if no data
        """
        try:
            data = self.metrics_socket.recv(flags=zmq.NOBLOCK)
            tti_msg = metrics_pb2.TtiMetrics()
            tti_msg.ParseFromString(data)
            
            self.current_tti = tti_msg.tti_index
            
            # Log received metrics every 500 TTIs
            if (self.current_tti % 500) == 0:
                rntis = [ue.rnti for ue in tti_msg.ues]
                print(f"[MCS RX] TTI={self.current_tti} UEs={len(rntis)} RNTIs={rntis}")
            
            # Build UE metrics dictionary
            ue_data = {}
            for ue in tti_msg.ues:
                mac = ue.mac
                ue_data[ue.rnti] = {
                    'CQI': mac.cqi,
                    'SNR': mac.snr,
                    'Backlog': mac.dl_buffer,
                    'Tx_brate': mac.dl_acked_bytes,
                    'UL_buffer': mac.ul_buffer,
                    'dl_prbs': mac.dl_prbs,
                    'dl_mcs': mac.dl_mcs,
                }
            
            self.last_metrics = ue_data
            return ue_data
            
        except zmq.Again:
            pass
        except Exception as e:
            print(f"[MCS muApp] Metrics error: {e}")
        
        return self.last_metrics if self.last_metrics else None
    
    def get_tti(self) -> int:
        """Get current TTI index."""
        return self.current_tti
    
    def send_mcs(self, mcs_values: List[Tuple[int, int]], tti_offset: int = 0):
        """
        Send MCS values to RAN.
        
        Args:
            mcs_values: List of (RNTI, MCS) tuples
            tti_offset: Offset to apply to TTI (for testing staleness)
        """
        msg = control_mcs_pb2.McsControl()
        msg.ran_index = self.ran_index
        msg.tti_index = self.current_tti + tti_offset
        self.ran_index += 1
        
        for rnti, mcs in mcs_values:
            ue_mcs = msg.ue_mcs.add()
            ue_mcs.rnti = int(rnti)
            ue_mcs.mcs = int(mcs)
        
        serialized = msg.SerializeToString()
        self.mcs_socket.send(serialized)
        
        # Log every 500 TTIs
        if (self.current_tti % 500) == 0:
            print(f"[MCS TX] TTI={self.current_tti + tti_offset} mcs: {mcs_values}")
    
    def close(self):
        """Clean up ZMQ resources."""
        self.mcs_socket.close()
        self.metrics_socket.close()
        self.context.term()


# ============================================================================
# MCS Algorithms
# ============================================================================

def fixed_mcs(ue_data: Dict[int, dict], mcs_value: int) -> List[Tuple[int, int]]:
    """
    Fixed MCS: Same MCS for all UEs.
    
    Args:
        ue_data: Dictionary of UE metrics
        mcs_value: MCS value to use (0-28)
    
    Returns:
        List of (RNTI, MCS) tuples
    """
    return [(rnti, mcs_value) for rnti in ue_data.keys()]


def random_mcs(ue_data: Dict[int, dict], min_mcs: int = 10, max_mcs: int = 20) -> List[Tuple[int, int]]:
    """
    Random MCS: Random MCS between min and max for each UE.
    
    Args:
        ue_data: Dictionary of UE metrics
        min_mcs: Minimum MCS value
        max_mcs: Maximum MCS value
    
    Returns:
        List of (RNTI, MCS) tuples
    """
    return [(rnti, random.randint(min_mcs, max_mcs)) for rnti in ue_data.keys()]


def cqi_based_mcs(ue_data: Dict[int, dict]) -> List[Tuple[int, int]]:
    """
    CQI-based MCS: Map CQI to MCS (roughly).
    CQI 0-5: MCS 0-9, CQI 6-10: MCS 10-16, CQI 11-15: MCS 17-28
    
    Args:
        ue_data: Dictionary of UE metrics
    
    Returns:
        List of (RNTI, MCS) tuples
    """
    result = []
    for rnti, metrics in ue_data.items():
        cqi = metrics.get('CQI', 7)
        if cqi <= 5:
            mcs = cqi * 2  # 0-10
        elif cqi <= 10:
            mcs = 10 + (cqi - 5) * 1  # 10-15
        else:
            mcs = 15 + (cqi - 10) * 2  # 15-25
        mcs = min(28, max(0, mcs))
        result.append((rnti, mcs))
    return result


# ============================================================================
# Main Loop
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='EdgeRIC MCS muApp')
    parser.add_argument('--algorithm', '-a', choices=['fixed', 'random', 'cqi'],
                        default='fixed', help='MCS algorithm')
    parser.add_argument('--mcs', type=int, default=20,
                        help='MCS value for fixed algorithm (0-28)')
    parser.add_argument('--min-mcs', type=int, default=10,
                        help='Min MCS for random algorithm')
    parser.add_argument('--max-mcs', type=int, default=20,
                        help='Max MCS for random algorithm')
    parser.add_argument('--tti-offset', type=int, default=0,
                        help='TTI offset for testing staleness')
    
    args = parser.parse_args()
    
    messenger = McsMessenger()
    
    print(f"[MCS muApp] Algorithm: {args.algorithm}")
    if args.algorithm == 'fixed':
        print(f"[MCS muApp] Fixed MCS: {args.mcs}")
    elif args.algorithm == 'random':
        print(f"[MCS muApp] Random MCS range: [{args.min_mcs}, {args.max_mcs}]")
    if args.tti_offset != 0:
        print(f"[MCS muApp] TTI offset: {args.tti_offset} (for staleness testing)")
    
    print("[MCS muApp] Waiting for metrics... Press Ctrl+C to stop.")
    
    try:
        while True:
            ue_data = messenger.get_metrics()
            
            if ue_data and len(ue_data) > 0:
                # Compute MCS values based on algorithm
                if args.algorithm == 'fixed':
                    mcs_values = fixed_mcs(ue_data, args.mcs)
                elif args.algorithm == 'random':
                    mcs_values = random_mcs(ue_data, args.min_mcs, args.max_mcs)
                elif args.algorithm == 'cqi':
                    mcs_values = cqi_based_mcs(ue_data)
                else:
                    mcs_values = fixed_mcs(ue_data, 20)
                
                # Send MCS values
                messenger.send_mcs(mcs_values, args.tti_offset)
            
            time.sleep(0.001)  # 1ms interval
            
    except KeyboardInterrupt:
        print("\n[MCS muApp] Exiting...")
    finally:
        messenger.close()


if __name__ == '__main__':
    main()
