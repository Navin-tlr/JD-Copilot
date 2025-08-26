import 'package:cloud_firestore/cloud_firestore.dart';
import '../firebase_config.dart';


class ChatMessage {
  final String id;
  final String senderId;
  final String senderName;
  final String message;
  final DateTime timestamp;
  final String? specialization;
  final bool isUserMessage;

  ChatMessage({
    required this.id,
    required this.senderId,
    required this.senderName,
    required this.message,
    required this.timestamp,
    this.specialization,
    required this.isUserMessage,
  });

  factory ChatMessage.fromFirestore(Map<String, dynamic> data, String id) {
    return ChatMessage(
      id: id,
      senderId: data['senderId'] ?? '',
      senderName: data['senderName'] ?? '',
      message: data['message'] ?? '',
      timestamp: (data['timestamp'] as Timestamp?)?.toDate() ?? DateTime.now(),
      specialization: data['specialization'],
      isUserMessage: data['isUserMessage'] ?? false,
    );
  }

  Map<String, dynamic> toFirestore() {
    return {
      'senderId': senderId,
      'senderName': senderName,
      'message': message,
      'timestamp': timestamp,
      'specialization': specialization,
      'isUserMessage': isUserMessage,
    };
  }
}

class ChatService {
  final FirebaseFirestore _firestore = FirebaseConfig.firestore;

  // Get chat messages for a user
  Stream<List<ChatMessage>> getChatMessages(String userId) {
    return _firestore
        .collection('users')
        .doc(userId)
        .collection('chat')
        .orderBy('timestamp', descending: true)
        .snapshots()
        .map((snapshot) {
      return snapshot.docs.map((doc) {
        return ChatMessage.fromFirestore(doc.data(), doc.id);
      }).toList();
    });
  }

  // Send a user message
  Future<void> sendUserMessage({
    required String userId,
    required String message,
    required String specialization,
  }) async {
    try {
      // Add user message to Firestore
      await _firestore
          .collection('users')
          .doc(userId)
          .collection('chat')
          .add({
        'senderId': userId,
        'senderName': 'You',
        'message': message,
        'timestamp': FieldValue.serverTimestamp(),
        'specialization': specialization,
        'isUserMessage': true,
      });

      // TODO: Here you would typically call your AI/LLM service
      // For now, we'll add a placeholder response
      await _addAIResponse(userId, message, specialization);
    } catch (e) {
      throw 'Failed to send message: $e';
    }
  }

  // Add AI response (placeholder for now)
  Future<void> _addAIResponse(
    String userId,
    String userMessage,
    String specialization,
  ) async {
    try {
      // This is a placeholder response
      // In a real app, you would call your AI service here
      String aiResponse = _generatePlaceholderResponse(userMessage, specialization);

      await _firestore
          .collection('users')
          .doc(userId)
          .collection('chat')
          .add({
        'senderId': 'ai',
        'senderName': 'Y² Assistant',
        'message': aiResponse,
        'timestamp': FieldValue.serverTimestamp(),
        'specialization': specialization,
        'isUserMessage': false,
      });
    } catch (e) {
      throw 'Failed to get AI response: $e';
    }
  }

  // Generate placeholder response (replace with actual AI integration)
  String _generatePlaceholderResponse(String userMessage, String specialization) {
    // Simple keyword-based responses for demonstration
    if (userMessage.toLowerCase().contains('hello') ||
        userMessage.toLowerCase().contains('hi')) {
      return 'Hello! I\'m your Y² Assistant. How can I help you with your $specialization journey today?';
    } else if (userMessage.toLowerCase().contains('help')) {
      return 'I\'m here to help! I can assist you with job search strategies, resume tips, interview preparation, and more. What specific area would you like to focus on?';
    } else if (userMessage.toLowerCase().contains('resume')) {
      return 'Great question about resumes! I can help you create a compelling resume that highlights your $specialization skills. Would you like me to review your current resume or help you create a new one?';
    } else if (userMessage.toLowerCase().contains('interview')) {
      return 'Interview preparation is crucial! I can help you with common $specialization interview questions, behavioral questions, and tips to make a great impression. What type of interview are you preparing for?';
    } else {
      return 'Thank you for your message! I\'m here to support your $specialization career goals. Feel free to ask me anything about job searching, career development, or industry insights.';
    }
  }

  // Clear chat history for a user
  Future<void> clearChatHistory(String userId) async {
    try {
      QuerySnapshot messages = await _firestore
          .collection('users')
          .doc(userId)
          .collection('chat')
          .get();

      WriteBatch batch = _firestore.batch();
      for (DocumentSnapshot doc in messages.docs) {
        batch.delete(doc.reference);
      }
      await batch.commit();
    } catch (e) {
      throw 'Failed to clear chat history: $e';
    }
  }

  // Get chat statistics for a user
  Future<Map<String, dynamic>> getChatStats(String userId) async {
    try {
      QuerySnapshot messages = await _firestore
          .collection('users')
          .doc(userId)
          .collection('chat')
          .get();

      int totalMessages = messages.docs.length;
      int userMessages = messages.docs
          .where((doc) => (doc.data() as Map<String, dynamic>?)?['isUserMessage'] == true)
          .length;
      int aiMessages = totalMessages - userMessages;

      return {
        'totalMessages': totalMessages,
        'userMessages': userMessages,
        'aiMessages': aiMessages,
      };
    } catch (e) {
      throw 'Failed to get chat statistics: $e';
    }
  }
}
