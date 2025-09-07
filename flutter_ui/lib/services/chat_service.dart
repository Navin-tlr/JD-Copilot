import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/chat_message.dart';
import '../models/chat_session.dart';

class ChatService {
  static const String _baseUrl = 'http://localhost:8000';
  
  // Create a new chat session
  Future<ChatSession> createSession(String userId, {String model = 'gpt-4'}) async {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/chat/sessions'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'model': model,
        }),
      );

      if (response.statusCode == 200) {
        return ChatSession.fromJson(jsonDecode(response.body));
      } else {
        throw Exception('Failed to create session: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error creating session: $e');
    }
  }

  // Get messages for a session
  Future<List<ChatMessage>> getSessionMessages(String sessionId) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/chat/sessions/$sessionId/messages'),
      );

      if (response.statusCode == 200) {
        final List<dynamic> messagesJson = jsonDecode(response.body);
        return messagesJson.map((json) => ChatMessage.fromJson(json)).toList();
      } else {
        throw Exception('Failed to get messages: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting messages: $e');
    }
  }

  // Send a message and get streaming response
  Stream<MessageChunk> sendMessage(String sessionId, String content, String userId) async* {
    try {
      final response = await http.post(
        Uri.parse('$_baseUrl/chat/send'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'session_id': sessionId,
          'content': content,
          'user_id': userId,
        }),
      );

      if (response.statusCode == 200) {
        // Parse Server-Sent Events
        final lines = response.body.split('\n');
        for (final line in lines) {
          if (line.startsWith('data: ')) {
            try {
              final data = line.substring(6); // Remove 'data: ' prefix
              final jsonData = jsonDecode(data);
              yield MessageChunk.fromJson(jsonData);
            } catch (e) {
              // Skip malformed lines
              continue;
            }
          }
        }
      } else {
        throw Exception('Failed to send message: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error sending message: $e');
    }
  }

  // Get user sessions
  Future<List<ChatSession>> getUserSessions(String userId) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/chat/sessions/$userId'),
      );

      if (response.statusCode == 200) {
        final List<dynamic> sessionsJson = jsonDecode(response.body);
        return sessionsJson.map((json) => ChatSession.fromJson(json)).toList();
      } else {
        throw Exception('Failed to get sessions: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error getting sessions: $e');
    }
  }

  // Delete a session
  Future<void> deleteSession(String sessionId) async {
    try {
      final response = await http.delete(
        Uri.parse('$_baseUrl/chat/sessions/$sessionId'),
      );

      if (response.statusCode != 200) {
        throw Exception('Failed to delete session: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error deleting session: $e');
    }
  }
}

// Message chunk for streaming responses
class MessageChunk {
  final String type;
  final String? content;
  final String? messageId;
  final String? timestamp;
  final String? sessionId;
  final String? error;

  const MessageChunk({
    required this.type,
    this.content,
    this.messageId,
    this.timestamp,
    this.sessionId,
    this.error,
  });

  factory MessageChunk.fromJson(Map<String, dynamic> json) {
    return MessageChunk(
      type: json['type'] as String,
      content: json['content'] as String?,
      messageId: json['message_id'] as String?,
      timestamp: json['timestamp'] as String?,
      sessionId: json['session_id'] as String?,
      error: json['error'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'content': content,
      'message_id': messageId,
      'timestamp': timestamp,
      'session_id': sessionId,
      'error': error,
    };
  }
}
