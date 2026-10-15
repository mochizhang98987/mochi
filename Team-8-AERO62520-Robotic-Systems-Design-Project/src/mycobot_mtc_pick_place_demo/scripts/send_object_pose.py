#!/usr/bin/env python3
"""
发送物体坐标到MTC抓取节点
Send object coordinates to MTC grasp node for coordinate-based grasping
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import argparse
import sys


class ObjectPosePublisher(Node):
    def __init__(self):
        super().__init__('object_pose_publisher')
        self.publisher = self.create_publisher(
            PoseStamped,
            '/object_pose',
            10
        )
        self.get_logger().info('物体坐标发布节点已启动')
    
    def send_pose(self, x, y, z, frame_id='base_link'):
        """发送物体坐标（单位：米）"""
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        
        msg.pose.position.x = x
        msg.pose.position.y = y
        msg.pose.position.z = z
        
        # 默认方向（不影响顶抓）
        msg.pose.orientation.x = 0.0
        msg.pose.orientation.y = 0.0
        msg.pose.orientation.z = 0.0
        msg.pose.orientation.w = 1.0
        
        self.publisher.publish(msg)
        self.get_logger().info(f'✅ 已发送物体坐标: X={x:.3f}m, Y={y:.3f}m, Z={z:.3f}m')
        self.get_logger().info(f'   (坐标系: {frame_id})')
        self.get_logger().info('   MTC节点将开始规划抓取轨迹...')


# 预设测试位置（适合MyCobot工作空间）
PRESETS = {
    'front': {
        'x': 0.20,
        'y': 0.0,
        'z': 0.05,
        'description': '前方地面位置（低）'
    },
    'front_high': {
        'x': 0.18,
        'y': 0.0,
        'z': 0.15,
        'description': '前方较高位置'
    },
    'left': {
        'x': 0.15,
        'y': 0.10,
        'z': 0.08,
        'description': '左前方位置'
    },
    'right': {
        'x': 0.15,
        'y': -0.10,
        'z': 0.08,
        'description': '右前方位置'
    },
    'near': {
        'x': 0.12,
        'y': 0.0,
        'z': 0.10,
        'description': '靠近位置（容易到达）'
    },
}


def main(args=None):
    parser = argparse.ArgumentParser(description='发送物体坐标给MTC抓取节点')
    parser.add_argument('--preset', type=str, choices=list(PRESETS.keys()),
                        help='使用预设位置: ' + ', '.join(PRESETS.keys()))
    parser.add_argument('--x', type=float, help='物体X坐标（米）')
    parser.add_argument('--y', type=float, help='物体Y坐标（米）')
    parser.add_argument('--z', type=float, help='物体Z坐标（米）')
    parser.add_argument('--frame', type=str, default='base_link',
                        help='参考坐标系（默认: base_link）')
    parser.add_argument('--list', action='store_true',
                        help='列出所有预设位置')
    
    # 解析参数
    if '--ros-args' in sys.argv:
        ros_args_idx = sys.argv.index('--ros-args')
        parsed_args = parser.parse_args(sys.argv[1:ros_args_idx])
    else:
        parsed_args = parser.parse_args()
    
    # 列出预设位置
    if parsed_args.list:
        print("\n📍 可用的预设位置:")
        print("-" * 60)
        for name, preset in PRESETS.items():
            print(f"  {name:12s} - {preset['description']}")
            print(f"               X={preset['x']:.2f}m, Y={preset['y']:.2f}m, Z={preset['z']:.2f}m")
        print("-" * 60)
        print("\n使用方法:")
        print(f"  ros2 run mycobot_mtc_pick_place_demo send_object_pose.py --preset front")
        print(f"  ros2 run mycobot_mtc_pick_place_demo send_object_pose.py --x 0.2 --y 0.0 --z 0.1")
        print("\n推荐工作空间范围:")
        print(f"  X: 0.12 ~ 0.25 米（前方）")
        print(f"  Y: -0.15 ~ 0.15 米（左右）")
        print(f"  Z: 0.05 ~ 0.20 米（高度，相对base_link）")
        return
    
    rclpy.init(args=args)
    node = ObjectPosePublisher()
    
    # 确定目标坐标
    if parsed_args.preset:
        preset = PRESETS[parsed_args.preset]
        x, y, z = preset['x'], preset['y'], preset['z']
        node.get_logger().info(f'使用预设位置: {parsed_args.preset} - {preset["description"]}')
    elif parsed_args.x is not None and parsed_args.y is not None and parsed_args.z is not None:
        x, y, z = parsed_args.x, parsed_args.y, parsed_args.z
        node.get_logger().info('使用自定义坐标')
    else:
        # 默认使用near预设（最容易到达）
        node.get_logger().warn('未指定坐标，使用默认预设: near')
        preset = PRESETS['near']
        x, y, z = preset['x'], preset['y'], preset['z']
    
    # 等待节点完全启动
    rclpy.spin_once(node, timeout_sec=0.5)
    
    # 发送目标
    node.send_pose(x, y, z, parsed_args.frame)
    
    # 再等待确保消息发送
    rclpy.spin_once(node, timeout_sec=1.0)
    
    node.get_logger().info('✅ 坐标已发送！请在RViz中观察MTC规划结果')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
