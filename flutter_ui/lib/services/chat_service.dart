import 'dart:convert';
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_markdown/flutter_markdown.dart';

enum MessageType { user, bot, loading, error }

class ChatService extends ChangeNotifier {
  static const String baseUrl = 'http://127.0.0.1:8001';

  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isConnected = false;
  bool _thinkingExiting = false;
  String _loadingMessage = 'Working on it…';

  List<ChatMessage> get messages => _messages;
  bool get isLoading => _isLoading;
  String get loadingMessage => _loadingMessage;
  bool get isConnected => _isConnected;
  bool get thinkingExiting => _thinkingExiting;

  ChatService() {
    // Attempt to ping backend on startup
    _pingBackend();
  }

  // Add a message to the chat (compat with UI expectations)
  void addMessage(String text, bool isUser, {MessageType? type, List<Map<String, dynamic>>? snippets}) {
    _messages.add(ChatMessage(
      text: text,
      sender: isUser ? 'user' : 'assistant',
      type: type ?? (isUser ? MessageType.user : MessageType.bot),
      timestamp: DateTime.now(),
      snippets: snippets, // Pass snippets to the message
    ));
    notifyListeners();
  }

  Future<void> _pingBackend() async {
    try {
      final resp = await http.get(Uri.parse('$baseUrl/health')).timeout(const Duration(seconds: 3));
      _isConnected = resp.statusCode == 200;
    } catch (_) {
      _isConnected = false;
    }
    notifyListeners();
  }

  Future<void> reconnect() async {
    await _pingBackend();
  }

  // Send a message and get response from the AI agent
  Future<void> sendMessage(String message) async {
    if (message.trim().isEmpty) return;
    
    // Add user message
    addMessage(message, true, type: MessageType.user);
    
    // Set loading state
    _isLoading = true;
    _loadingMessage = 'Working on it…';
    _thinkingExiting = false;
    // Add a transient loading message for the UI bubble
    _messages.add(ChatMessage(
      text: _loadingMessage,
      sender: 'assistant',
      type: MessageType.loading,
      timestamp: DateTime.now(),
    ));
    notifyListeners();
    
    try {
      // ensure backend connectivity state is fresh
      if (!_isConnected) {
        await _pingBackend();
      }
      
      print('🔍 Sending request to: $baseUrl/chat');
      print('🔍 Request body: ${json.encode({"question": message, "session_id": "default"})}');
      
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'question': message,
          'session_id': 'default'
        }),
      );
      
      print('🔍 Response status: ${response.statusCode}');
      print('🔍 Response body: ${response.body}');
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Check if the response contains an error flag
        if (data['error'] == true) {
          // It's a structured error from our backend
          final errorMessage = data['answer'] ?? 'An error occurred';
          _thinkingExiting = true;
          notifyListeners();
          await Future.delayed(const Duration(milliseconds: 250));
          _removeLastLoadingMessageIfAny();
          addMessage(errorMessage, false, type: MessageType.error);
          return;
        }
        
        final answer = data['answer'] ?? 'No response received';
        
        // Strip emojis from the answer
        final cleanAnswer = _stripEmojis(answer);

        // Get snippets if available
        List<Map<String, dynamic>>? snippets;
        if (data['snippets'] != null && data['snippets'] is List) {
          snippets = List<Map<String, dynamic>>.from(data['snippets']);
        }

        // Begin exit for thinking animation, then replace loading bubble
        _thinkingExiting = true;
        notifyListeners();
        await Future.delayed(const Duration(milliseconds: 250));
        _removeLastLoadingMessageIfAny();
        addMessage(cleanAnswer, false, type: MessageType.bot, snippets: snippets);
        
        // Remove the old citations table logic since we're using snippets now
        
      } else {
        _thinkingExiting = true;
        notifyListeners();
        await Future.delayed(const Duration(milliseconds: 250));
        _removeLastLoadingMessageIfAny();
        addMessage('Sorry, I encountered an error. Please try again.', false, type: MessageType.error);
      }
    } catch (e) {
      print('❌ Error in sendMessage: $e');
      _thinkingExiting = true;
      notifyListeners();
      await Future.delayed(const Duration(milliseconds: 250));
      _removeLastLoadingMessageIfAny();
      addMessage('Connection error: $e', false, type: MessageType.error);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void _removeLastLoadingMessageIfAny() {
    for (int i = _messages.length - 1; i >= 0; i--) {
      if (_messages[i].type == MessageType.loading) {
        _messages.removeAt(i);
        break;
      }
    }
  }
  
  // Strip emojis from text
  String _stripEmojis(String text) {
    // Remove common emojis and emoticons using valid Dart regex syntax
    return text
        .replaceAll(RegExp(r'[\u{1F600}-\u{1F64F}]', unicode: true), '') // Emoticons
        .replaceAll(RegExp(r'[\u{1F300}-\u{1F5FF}]', unicode: true), '') // Misc symbols
        .replaceAll(RegExp(r'[\u{1F680}-\u{1F6FF}]', unicode: true), '') // Transport
        .replaceAll(RegExp(r'[\u{1F1E0}-\u{1F1FF}]', unicode: true), '') // Flags
        .replaceAll(RegExp(r'[\u{2600}-\u{26FF}]', unicode: true), '') // Misc symbols
        .replaceAll(RegExp(r'[\u{2700}-\u{27BF}]', unicode: true), '') // Dingbats
        .trim();
  }
  
  // Build citations table in markdown format
  String _buildCitationsTable(List<dynamic> citations) {
    if (citations.isEmpty) return '';
    
    // Filter out citations without meaningful data
    final validCitations = citations.where((citation) {
      final company = citation['company']?.toString().trim() ?? '';
      final role = citation['role']?.toString().trim() ?? '';
      final year = citation['year']?.toString().trim() ?? '';
      return company.isNotEmpty || role.isNotEmpty || year.isNotEmpty;
    }).toList();
    
    if (validCitations.isEmpty) return '';
    
    StringBuffer table = StringBuffer();
    table.writeln('## Sources & Citations');
    table.writeln('');
    table.writeln('| Company | Role | Year | Skills |');
    table.writeln('|---------|------|------|--------|');
    
    for (final citation in validCitations) {
      final company = citation['company']?.toString().trim() ?? '-';
      final role = citation['role']?.toString().trim() ?? '-';
      final year = citation['year']?.toString().trim() ?? '-';
      
      // Handle skills array
      String skills = '-';
      if (citation['extracted_skills'] != null) {
        final skillsList = citation['extracted_skills'] as List;
        if (skillsList.isNotEmpty) {
          skills = skillsList.take(3).join(', '); // Show first 3 skills
          if (skillsList.length > 3) {
            skills += '...';
          }
        }
      }
      
      table.writeln('| $company | $role | $year | $skills |');
    }
    
    return table.toString();
  }
  
  // Clear chat history
  void clearChat() {
    _messages.clear();
    notifyListeners();
  }
  
  // Update loading message
  void updateLoadingMessage(String message) {
    _loadingMessage = message;
    notifyListeners();
  }
}

class ChatMessage {
  final String text;
  final String sender; // 'user' or 'assistant'
  final MessageType type;
  final DateTime timestamp;
  final List<Map<String, dynamic>>? snippets; // Add snippets to the message
  
  ChatMessage({
    required this.text,
    required this.sender,
    required this.type,
    required this.timestamp,
    this.snippets, // Initialize snippets
  });
}
