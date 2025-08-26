import 'package:cloud_firestore/cloud_firestore.dart';

class UserModel {
  final String uid;
  final String fullName;
  final String email;
  final String specialization;
  final DateTime createdAt;
  final DateTime? lastLoginAt;
  final DateTime? updatedAt;

  UserModel({
    required this.uid,
    required this.fullName,
    required this.email,
    required this.specialization,
    required this.createdAt,
    this.lastLoginAt,
    this.updatedAt,
  });

  // Create from Firestore document
  factory UserModel.fromFirestore(Map<String, dynamic> data, String uid) {
    return UserModel(
      uid: uid,
      fullName: data['fullName'] ?? '',
      email: data['email'] ?? '',
      specialization: data['specialization'] ?? '',
      createdAt: (data['createdAt'] as Timestamp?)?.toDate() ?? DateTime.now(),
      lastLoginAt: (data['lastLoginAt'] as Timestamp?)?.toDate(),
      updatedAt: (data['updatedAt'] as Timestamp?)?.toDate(),
    );
  }

  // Convert to Map for Firestore
  Map<String, dynamic> toFirestore() {
    return {
      'fullName': fullName,
      'email': email,
      'specialization': specialization,
      'createdAt': createdAt,
      'lastLoginAt': lastLoginAt,
      'updatedAt': updatedAt,
    };
  }

  // Create a copy with updated fields
  UserModel copyWith({
    String? fullName,
    String? specialization,
    DateTime? lastLoginAt,
    DateTime? updatedAt,
  }) {
    return UserModel(
      uid: uid,
      fullName: fullName ?? this.fullName,
      email: email,
      specialization: specialization ?? this.specialization,
      createdAt: createdAt,
      lastLoginAt: lastLoginAt ?? this.lastLoginAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  @override
  String toString() {
    return 'UserModel(uid: $uid, fullName: $fullName, email: $email, specialization: $specialization)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is UserModel && other.uid == uid;
  }

  @override
  int get hashCode => uid.hashCode;
}
