import 'package:flutter/material.dart';
import 'backend_service.dart';

class ChatMessage {
  final String sender; // 'user' or 'bot'
  final String text;
  final DateTime timestamp;
  final MessageType type;
  final Map<String, dynamic>? metadata;

  ChatMessage({
    required this.sender,
    required this.text,
    required this.timestamp,
    this.type = MessageType.text,
    this.metadata,
  });
}

enum MessageType {
  text,
  error,
  loading,
  stats,
  companies,
  skills,
}

class ChatService extends ChangeNotifier {
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isConnected = false;
  bool _thinkingExiting = false;

  List<ChatMessage> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;
  bool get isConnected => _isConnected;
  bool get thinkingExiting => _thinkingExiting;

  ChatService() {
    _initializeChat();
  }

  String _stripEmojis(String input) {
    final emojiRegex = RegExp(
      r"[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F900}-\u{1F9FF}\u{1FA70}-\u{1FAFF}\u{FE0F}]",
      unicode: true,
    );
    return input.replaceAll(emojiRegex, '');
  }

  void _initializeChat() async {
    // Check backend connection
    _isConnected = await BackendService.checkHealth();
    notifyListeners();

    if (_isConnected) {
      _addBotMessage(
        "Hello! I'm your JD Copilot assistant. I can help you with:\n\n"
        "• Placement statistics and insights\n"
        "• Company information and comparisons\n"
        "• Skills analysis and recommendations\n"
        "• Resume matching with job descriptions\n"
        "• GD simulation and feedback\n\n"
        "What would you like to know?",
      );
    } else {
      _addBotMessage(
        "Backend connection failed. Please ensure the server is running on http://127.0.0.1:8000",
        type: MessageType.error,
      );
    }
  }

  void _addBotMessage(String text, {MessageType type = MessageType.text}) {
    final cleaned = _stripEmojis(text);
    _messages.insert(0, ChatMessage(
      sender: 'bot',
      text: cleaned,
      timestamp: DateTime.now(),
      type: type,
    ));
    notifyListeners();
  }

  void _addUserMessage(String text) {
    _messages.insert(0, ChatMessage(
      sender: 'user',
      text: text,
      timestamp: DateTime.now(),
    ));
    notifyListeners();
  }

  void _addLoadingMessage() {
    _thinkingExiting = false;
    _isLoading = true;
    _messages.insert(0, ChatMessage(
      sender: 'bot',
      text: 'Working on it…',
      timestamp: DateTime.now(),
      type: MessageType.loading,
    ));
    notifyListeners();
  }

  void _removeLoadingMessage() {
    _isLoading = false;
    _messages.removeWhere((msg) => msg.type == MessageType.loading);
    notifyListeners();
  }

  Future<void> sendMessage(String text) async {
    if (text.trim().isEmpty) return;

    _addUserMessage(text);
    
    if (!_isConnected) {
      _addBotMessage(
        "Cannot connect to backend. Please check if the server is running.",
        type: MessageType.error,
      );
      return;
    }

    _addLoadingMessage();

    try {
      // Analyze the message to determine the best backend endpoint
      final response = await _processMessage(text);
      // Begin graceful exit: trigger fade-out
      _thinkingExiting = true;
      notifyListeners();
      await Future.delayed(const Duration(milliseconds: 250));
      _removeLoadingMessage();
      _addBotMessage(response);
    } catch (e) {
      _thinkingExiting = true;
      notifyListeners();
      await Future.delayed(const Duration(milliseconds: 250));
      _removeLoadingMessage();
      _addBotMessage(
        "Error: ${e.toString()}",
        type: MessageType.error,
      );
    }
  }

  Future<String> _processMessage(String text) async {
    // Use the main LLM endpoint for ALL queries - it's smarter!
    return await _handleGeneralQuery(text);
  }

  // Unused specialized handlers retained for future routing; commented to satisfy lints
  // Future<String> _handleCompanyQuery(String text) async {
  //   try {
  //     final companies = await BackendService.getCompanies();
  //     final companyStats = await BackendService.getCompanyStats();
      
  //     return "Company Information\n\n"
  //         "Total Companies: ${companies.length}\n"
  //         "Active Companies: ${companies.take(10).join(', ')}${companies.length > 10 ? '...' : ''}\n\n"
  //         "Top Recruiters:\n"
  //         "${companyStats['top_companies']?.map((c) => '• ${c['name']}: ${c['count']} placements').join('\n') ?? 'Data not available'}\n\n"
  //         "Ask me about specific companies or placement trends!";
  //   } catch (e) {
  //     return "Failed to fetch company information: ${e.toString()}";
  //   }
  // }

  // Future<String> _handleStatsQuery(String text) async {
  //   try {
  //     final placementStats = await BackendService.getPlacementStats();
      
  //     return "Placement Statistics\n\n"
  //         "Total Placements: ${placementStats['total_placements'] ?? 'N/A'}\n"
  //         "Average Package: ${placementStats['average_package'] ?? 'N/A'}\n"
  //         "Highest Package: ${placementStats['highest_package'] ?? 'N/A'}\n"
  //         "Placement Rate: ${placementStats['placement_rate'] ?? 'N/A'}%\n\n"
  //         "Top Specializations:\n"
  //         "${placementStats['top_specializations']?.map((s) => '• ${s['name']}: ${s['count']} students').join('\n') ?? 'Data not available'}";
  //   } catch (e) {
  //     return "Failed to fetch statistics: ${e.toString()}";
  //   }
  // }

  // Future<String> _handleSkillsQuery(String text) async {
  //   try {
  //     // Extract skills from the query
  //     final skills = await BackendService.searchSkills(text);
      
  //     if (skills.isNotEmpty) {
  //       return "Skills Analysis\n\n"
  //           "Relevant Skills Found:\n"
  //           "${skills.map((skill) => '• $skill').join('\n')}\n\n"
  //           "Recommendation: Focus on developing these skills to improve your placement prospects.";
  //     } else {
  //       return "Skills Search\n\n"
  //           "I couldn't find specific skills matching your query. Try asking about:\n"
  //           "• Technical skills (Python, Java, etc.)\n"
  //           "• Soft skills (Leadership, Communication)\n"
  //           "• Domain-specific skills (AI/ML, Web Development)";
  //     }
  //   } catch (e) {
  //     return "Failed to search skills: ${e.toString()}";
  //   }
  // }

  // Future<String> _handleResumeQuery(String text) async {
  //   return "Resume Analysis\n\n"
  //       "I can help you analyze your resume and match it with job descriptions!\n\n"
  //       "To get started:\n"
  //       "1. Share your resume text or key skills\n"
  //       "2. I'll match it with available job descriptions\n"
  //       "3. Get personalized recommendations and upskilling plans\n\n"
  //       "Example: 'Analyze my resume for software engineering roles'";
  // }

  // Future<String> _handleGDQuery(String text) async {
  //   return "Group Discussion Simulation\n\n"
  //       "I can simulate and evaluate your GD performance!\n\n"
  //       "How it works:\n"
  //       "1. Share your GD transcript or key points\n"
  //       "2. I'll analyze your communication, logic, and leadership\n"
  //       "3. Get detailed feedback and improvement suggestions\n\n"
  //       "Example: 'Simulate my GD on AI ethics'";
  // }

  Future<String> _handleGeneralQuery(String text) async {
    try {
      final response = await BackendService.query(question: text);
      final answer = response['answer'] as String?;
      final snippets = (response['snippets'] as List?)?.cast<Map<String, dynamic>>() ?? const [];

      // Build grounded citations table from snippets metadata only (no guessing)
      final rows = <String>[];
      final seen = <String>{};
      for (final sn in snippets) {
        final meta = (sn['metadata'] as Map?)?.cast<String, dynamic>() ?? const {};
        final company = (meta['company'] ?? '').toString().trim();
        final role = (meta['role'] ?? '').toString().trim();
        final year = (meta['year'] ?? '').toString().trim();
        final skillsList = (meta['extracted_skills'] as List?)?.cast<String>() ?? const [];
        if (company.isEmpty && role.isEmpty && year.isEmpty && skillsList.isEmpty) continue;
        final key = [company, role, year, skillsList.take(3).join(',')].join('|');
        if (seen.contains(key)) continue;
        seen.add(key);
        final skills = skillsList.isNotEmpty ? skillsList.take(6).join(', ') : 'Not mentioned';
        rows.add('| ${company.isEmpty ? 'Not mentioned' : company} | ${role.isEmpty ? 'Not mentioned' : role} | ${year.isEmpty ? 'Not mentioned' : year} | $skills |');
      }

      String citations = '';
      final hasMeaningful = rows.any((r) => !r.contains('Not mentioned | Not mentioned | Not mentioned |'));
      if (rows.isNotEmpty && hasMeaningful) {
        citations = '\n\nCitations from job descriptions (grounded):\n\n'
            '| Company | Role | Year | Skills cited |\n'
            '|---|---|---|---|\n'
            '${rows.join('\n')}';
      }

      final safeAnswer = answer ?? "I couldn't find a specific answer to your question.";
      return safeAnswer + citations;
    } catch (e) {
      return "Query failed: ${e.toString()}";
    }
  }

  void clearChat() {
    _messages.clear();
    _initializeChat();
  }

  Future<void> reconnect() async {
    _isConnected = await BackendService.checkHealth();
    notifyListeners();
    
    if (_isConnected) {
      _addBotMessage("Backend connection restored!");
    }
  }
}
