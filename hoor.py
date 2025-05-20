#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from std_srvs.srv import Empty
import math
import sys

x = 0.0
y = 0.0
yaw = 0.0

def poseCallback(pose_message):
    """تحديث موضع وتوجه السلحفاة"""
    global x, y, yaw
    x = pose_message.x
    y = pose_message.y
    yaw = pose_message.theta

def is_within_bounds(x, y, margin=1.0):
    """التحقق من أن الموضع ضمن حدود النافذة"""
    return margin <= x <= 11 - margin and margin <= y <= 11 - margin

def move(velocity_publisher, speed, distance, is_forward):
    """تحريك السلحفاة في خط مستقيم"""
    velocity_message = Twist()
    global x, y
    x0 = x
    y0 = y

    velocity_message.linear.x = abs(speed) if is_forward else -abs(speed)
    velocity_message.angular.z = 0
    loop_rate = rospy.Rate(50)
    current_distance = 0.0

    while current_distance < distance:
        if not is_within_bounds(x, y):
            rospy.loginfo("السلحفاة وصلت حدود النافذة!")
            break

        velocity_publisher.publish(velocity_message)
        loop_rate.sleep()
        # ✅ التصحيح هنا
        current_distance = math.sqrt((x - x0) ** 2 + (y - y0) ** 2)
        rospy.loginfo(f"Distance traveled: {current_distance:.2f}")

    velocity_message.linear.x = 0
    velocity_publisher.publish(velocity_message)

def rotate(velocity_publisher, angular_speed_degree, relative_angle_degree, clockwise):
    """تدوير السلحفاة بزاوية محددة"""
    velocity_message = Twist()
    angular_speed = math.radians(abs(angular_speed_degree))
    velocity_message.angular.z = -angular_speed if clockwise else angular_speed

    t0 = rospy.Time.now().to_sec()
    current_angle = 0.0
    loop_rate = rospy.Rate(50)
    
    while current_angle < math.radians(relative_angle_degree):
        if not is_within_bounds(x, y):
            rospy.loginfo("السلحفاة وصلت حدود النافذة!")
            break
            
        velocity_publisher.publish(velocity_message)
        t1 = rospy.Time.now().to_sec()
        current_angle = angular_speed * (t1-t0)
        loop_rate.sleep()
    
    velocity_message.angular.z = 0
    velocity_publisher.publish(velocity_message)

def draw_square(velocity_publisher):
    """رسم مربع"""
    edge_length = float(input("أدخل طول ضلع المربع (<=5.0): "))
    if edge_length > 5.0:
        edge_length = 5.0
        rospy.logwarn("تم تصغير الطول إلى 5.0 لتجنب الحدود")
    
    for _ in range(4):
        move(velocity_publisher, 1.0, edge_length, True)
        rotate(velocity_publisher, 30, 90, False)

def draw_triangle(velocity_publisher):
    """رسم مثلث متساوي الأضلاع"""
    side_length = float(input("أدخل طول ضلع المثلث (<=6.0): "))
    if side_length > 6.0:
        side_length = 6.0
        rospy.logwarn("تم تصغير الطول إلى 6.0 لتجنب الحدود")
    
    for _ in range(3):
        move(velocity_publisher, 1.0, side_length, True)
        rotate(velocity_publisher, 30, 120, False)

def circular_trajectory(velocity_publisher):
    """رسم دائرة حسب الطلب"""
    radius = float(input("أدخل نصف قطر الدائرة: "))
    
    velocity_message = Twist()
    velocity_message.linear.x = radius
    velocity_message.angular.z = 1.5
    loop_rate = rospy.Rate(10)

    t0 = rospy.Time.now().to_sec()
    while (rospy.Time.now().to_sec() - t0 < 10) and (x > 0.7 and y > 0.7) and (x < 10.5 and y < 10.5):
        rospy.loginfo(f'x={x:.2f}, y={y:.2f}, radius={radius:.2f}')
        velocity_publisher.publish(velocity_message)
        loop_rate.sleep()

    velocity_message.linear.x = 0
    velocity_message.angular.z = 0
    velocity_publisher.publish(velocity_message)

def spiral_trajectory(velocity_publisher):
    """رسم شكل حلزوني"""
    rate_change = float(input("أدخل معدل تغير نصف القطر للحلزوني: "))
    
    velocity_message = Twist()
    rk = 0
    loop_rate = rospy.Rate(1)

    while (x > 0.7 and y > 0.7) and (x < 10.5 and y < 10.5):
        rk += rate_change
        velocity_message.linear.x = rk
        velocity_message.angular.z = 4
        velocity_publisher.publish(velocity_message)
        rospy.loginfo(f'x={x:.2f}, y={y:.2f}, rk={rk:.2f}')
        loop_rate.sleep()

    velocity_message.linear.x = 0
    velocity_message.angular.z = 0
    velocity_publisher.publish(velocity_message)

def go_to_point(velocity_publisher):
    """الانتقال إلى نقطة محددة"""
    x_goal = float(input("أدخل الإحداثي X للهدف (1-10): "))
    y_goal = float(input("أدخل الإحداثي Y للهدف (1-10): "))

    if not is_within_bounds(x_goal, y_goal):
        rospy.logerr("الإحداثيات خارج الحدود المسموحة!")
        return

    velocity_message = Twist()
    K_linear = 0.5
    K_angular = 4.0

    while True:
        # ✅ التصحيح هنا
        distance = math.sqrt((x_goal - x) ** 2 + (y_goal - y) ** 2)
        if distance < 0.1:
            break

        linear_speed = distance * K_linear
        desired_angle = math.atan2(y_goal - y, x_goal - x)
        angular_speed = (desired_angle - yaw) * K_angular

        velocity_message.linear.x = linear_speed
        velocity_message.angular.z = angular_speed
        velocity_publisher.publish(velocity_message)

        rospy.loginfo(f"المسافة المتبقية: {distance:.2f}")
        rospy.sleep(0.1)

    velocity_message.linear.x = 0
    velocity_message.angular.z = 0
    velocity_publisher.publish(velocity_message)

def draw_hexagon(velocity_publisher):
    """رسم شكل سداسي"""
    side_length = float(input("أدخل طول الضلع (<=3.0): "))
    if side_length > 3.0:
        side_length = 3.0
        rospy.logwarn("تم تصغير الطول إلى 3.0 لتجنب الحدود")
    
    for _ in range(6):
        move(velocity_publisher, 1.0, side_length, True)
        rotate(velocity_publisher, 30, 60, False)

def wave_motion(velocity_publisher):
    """حركة موجية (جيبي)"""
    amplitude = float(input("أدخل سعة الموجة (1.0-3.0): "))
    wavelength = float(input("أدخل الطول الموجي (1.0-5.0): "))
    
    velocity_message = Twist()
    velocity_message.linear.x = 1.0
    loop_rate = rospy.Rate(10)
    t0 = rospy.Time.now().to_sec()
    
    while is_within_bounds(x, y):
        t = rospy.Time.now().to_sec() - t0
        velocity_message.angular.z = amplitude * math.cos(2 * math.pi * t / wavelength)
        velocity_publisher.publish(velocity_message)
        loop_rate.sleep()
    
    velocity_message.linear.x = 0
    velocity_message.angular.z = 0
    velocity_publisher.publish(velocity_message)

def reset_turtle():
    """إعادة تعيين موضع السلحفاة"""
    rospy.wait_for_service('/reset')
    try:
        reset = rospy.ServiceProxy('/reset', Empty)
        reset()
        rospy.loginfo("تم إعادة تعيين موضع السلحفاة")
    except rospy.ServiceException as e:
        rospy.logerr(f"فشل استدعاء الخدمة: {e}")

def main():
    rospy.init_node('turtlesim_motion_controller', anonymous=True)
    velocity_publisher = rospy.Publisher('/turtle1/cmd_vel', Twist, queue_size=10)
    rospy.Subscriber('/turtle1/pose', Pose, poseCallback)
    rospy.sleep(1)  # انتظار لتلقي البيانات الأولية
    
    while not rospy.is_shutdown():
        print("\nاختر أحد مسارات الحركة للسلحفاة:")
        print("1. مربع")
        print("2. مثلث")
        print("3. دائرة")
        print("4. شكل حلزوني")
        print("5. الانتقال إلى نقطة")
        print("6. شكل سداسي")
        print("7. حركة موجية")
        print("8. إعادة التعيين")
        print("9. خروج")
        
        try:
            choice = int(input("أدخل اختيارك (1-9): "))
        except ValueError:
            print("الرجاء إدخال رقم صحيح!")
            continue
            
        if choice == 1:
            draw_square(velocity_publisher)
        elif choice == 2:
            draw_triangle(velocity_publisher)
        elif choice == 3:
            circular_trajectory(velocity_publisher)
        elif choice == 4:
            spiral_trajectory(velocity_publisher)
        elif choice == 5:
            go_to_point(velocity_publisher)
        elif choice == 6:
            draw_hexagon(velocity_publisher)
        elif choice == 7:
            wave_motion(velocity_publisher)
        elif choice == 8:
            reset_turtle()
        elif choice == 9:
            print("مع السلامة!")
            break
        else:
            print("اختيار غير صحيح، الرجاء المحاولة مرة أخرى")

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        rospy.loginfo("تم إنهاء البرنامج")