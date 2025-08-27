# Backend Integration Guide

## 🚀 **Overview**

This Flutter app is now fully integrated with your Python FastAPI backend! The integration provides:

- **Real-time chat** with intelligent message routing
- **Multiple backend endpoints** for different types of queries
- **Connection status monitoring** with automatic reconnection
- **Professional UI** with loading states and error handling

## 🔧 **Backend Setup**

### 1. **Start Your Python Backend**

```bash
# Navigate to your backend directory
cd ../app

# Activate virtual environment (if using one)
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r ../requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. **Verify Backend is Running**

- Open your browser and go to: `http://127.0.0.1:8000/docs`
- You should see the FastAPI Swagger documentation
- Test the health endpoint: `http://127.0.0.1:8000/health`

## 📱 **Frontend Features**

### **Connection Status Indicator**
- **Green dot + "Connected"**: Backend is reachable
- **Red dot + "Disconnected"**: Backend is unreachable
- **Reconnect button**: Manual reconnection attempt

### **Intelligent Message Routing**
The app automatically routes your messages to the most appropriate backend endpoint:

| **Message Type** | **Backend Endpoint** | **Example Queries** |
|------------------|----------------------|---------------------|
| **Companies** | `/companies`, `/stats/companies` | "Show me companies", "How many companies?" |
| **Statistics** | `/stats/placement` | "Placement stats", "How many students placed?" |
| **Skills** | `/search/skills` | "What skills are in demand?", "Python skills" |
| **Resume** | `/query/resume_match` | "Analyze my resume", "Resume matching" |
| **GD Simulation** | `/gd/simulate` | "Simulate GD", "Group discussion feedback" |
| **General** | `/query` | "Any other questions" |

### **Enhanced Chat Experience**
- **Loading states** with animated indicators
- **Error handling** with user-friendly messages
- **Rich formatting** for responses (bold, lists, emojis)
- **Automatic reconnection** attempts

## 🧪 **Testing the Integration**

### **1. Basic Connection Test**
1. Start your backend server
2. Launch the Flutter app
3. Check the connection status indicator (top-left)
4. Should show "Connected" with green dot

### **2. Test Different Query Types**

#### **Company Queries:**
```
"Show me all companies"
"How many companies are recruiting?"
"What are the top companies?"
```

#### **Statistics Queries:**
```
"Show placement statistics"
"How many students got placed?"
"What's the average package?"
```

#### **Skills Queries:**
```
"What skills are in demand?"
"Show me Python skills"
"Technical skills for software engineering"
```

#### **Resume Queries:**
```
"Help me with my resume"
"Resume analysis for software roles"
"Match my skills with job descriptions"
```

#### **GD Queries:**
```
"Simulate a GD on AI ethics"
"Group discussion feedback"
"GD preparation tips"
```

## 🔍 **Troubleshooting**

### **Connection Issues**

#### **"Disconnected" Status**
1. **Check if backend is running:**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. **Verify port and host:**
   - Backend should be on `127.0.0.1:8000`
   - Check for firewall/antivirus blocking

3. **Check backend logs:**
   - Look for error messages in terminal
   - Verify all dependencies are installed

#### **"Error: Could not connect"**
1. **Network issues:**
   - Ensure both devices are on same network
   - Check if using correct IP address

2. **Backend errors:**
   - Check backend terminal for Python errors
   - Verify database connections

### **Message Routing Issues**

#### **Wrong Endpoint Called**
- Check message content for keywords
- Verify backend endpoint exists
- Check backend logs for errors

#### **No Response**
- Verify backend is processing requests
- Check if endpoint returns proper JSON
- Look for Python exceptions in backend

## 🚀 **Advanced Features**

### **Custom Message Processing**
You can extend the `ChatService` to handle custom message types:

```dart
Future<String> _handleCustomQuery(String text) async {
  // Your custom logic here
  return "Custom response";
}
```

### **Adding New Endpoints**
1. Add method to `BackendService`
2. Add routing logic in `ChatService`
3. Update message handling

### **Real-time Updates**
The app uses `ChangeNotifier` for real-time UI updates:
- Messages appear instantly
- Connection status updates automatically
- Loading states are reactive

## 📊 **Backend Endpoints Used**

| **Endpoint** | **Method** | **Purpose** |
|--------------|------------|-------------|
| `/health` | GET | Connection check |
| `/query` | POST | General queries |
| `/companies` | GET | Company list |
| `/stats/placement` | GET | Placement statistics |
| `/stats/companies` | GET | Company statistics |
| `/search/skills` | GET | Skills search |
| `/specialization/insights` | GET | Specialization data |
| `/query/resume_match` | POST | Resume matching |
| `/gd/simulate` | POST | GD simulation |
| `/alerts` | GET | System alerts |

## 🎯 **Next Steps**

1. **Test all endpoints** with different query types
2. **Customize responses** in the backend
3. **Add authentication** if needed
4. **Implement caching** for better performance
5. **Add real-time notifications** for new alerts

## 📞 **Support**

If you encounter issues:
1. Check backend logs first
2. Verify network connectivity
3. Test endpoints directly with curl/Postman
4. Check Flutter console for error messages

---

**Happy coding! 🚀**
