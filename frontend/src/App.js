import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Avatar,
  Chip,
  CircularProgress,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Card,
  CardContent,
  Grid,
  AppBar,
  Toolbar,
  Tooltip,
  ThemeProvider,
  createTheme,
  CssBaseline,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Memory as MemoryIcon,
  Psychology as PsychologyIcon,
  History as HistoryIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  Mood as MoodIcon,
  MoodBad as MoodBadIcon,
  SentimentSatisfied as NeutralIcon,
  EmojiEmotions as HappyIcon,
  Favorite as LoveIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { format } from 'date-fns';
import './App.css';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8007';

// Create custom theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#6366f1',
      light: '#818cf8',
      dark: '#4f46e5',
    },
    secondary: {
      main: '#8b5cf6',
      light: '#a78bfa',
      dark: '#7c3aed',
    },
    background: {
      default: '#0f172a',
      paper: '#1e293b',
    },
    success: {
      main: '#10b981',
    },
    info: {
      main: '#0ea5e9',
    },
    warning: {
      main: '#f59e0b',
    },
    error: {
      main: '#ef4444',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
});

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState(() => {
    const saved = localStorage.getItem('empathai_user_id');
    return saved || `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  });
  const [sessionId, setSessionId] = useState(null);
  const [memories, setMemories] = useState([]);
  const [userInfo, setUserInfo] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [typing, setTyping] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [apiStatus, setApiStatus] = useState('checking');
  const messagesEndRef = useRef(null);

  // Emotion configuration
  const emotionConfig = {
    joy: { icon: <HappyIcon />, color: 'success', label: 'Joy' },
    sadness: { icon: <MoodBadIcon />, color: 'info', label: 'Sadness' },
    neutral: { icon: <NeutralIcon />, color: 'warning', label: 'Neutral' },
    curiosity: { icon: <PsychologyIcon />, color: 'secondary', label: 'Curiosity' },
    excitement: { icon: <MoodIcon />, color: 'success', label: 'Excitement' },
    anger: { icon: <MoodBadIcon />, color: 'error', label: 'Anger' },
    love: { icon: <LoveIcon />, color: 'error', label: 'Love' }
  };

  // Check API status on startup with useCallback
  const checkApiStatus = useCallback(async () => {
    console.log('🔍 Checking backend at:', `${API_BASE_URL}/health`);
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      console.log('✅ Backend response:', response.data);
      if (response.data.status === 'healthy') {
        setApiStatus('connected');
        showSnackbar('Connected to EmpathAI backend', 'success');
      } else {
        setApiStatus('disconnected');
        showSnackbar(`Backend status: ${response.data.status}`, 'warning');
      }
    } catch (error) {
      console.error('❌ Backend connection error:', error);
      setApiStatus('disconnected');
      showSnackbar('Backend not connected. Please start the server.', 'error');
    }
  }, []);

  // Load user information with useCallback
  const loadUserInfo = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/user/${userId}`);
      console.log('👤 User info:', response.data);
      setUserInfo(response.data);
    } catch (error) {
      console.log('No existing user data found:', error.message);
      setUserInfo({
        user_id: userId,
        exists: false,
        total_conversations: 0,
        memory_count: 0
      });
    }
  }, [userId]);

  // Load memories with useCallback - FIXED with safe access
  const loadMemories = useCallback(async () => {
    try {
      console.log('🧠 Loading memories for:', userId);
      const response = await axios.get(`${API_BASE_URL}/user/${userId}/memories?limit=10`);
      console.log('📦 Memories response:', response.data);
      
      // Safe extraction of memories array
      const memoriesData = response.data?.memories || response.data || [];
      console.log('📝 Processed memories:', memoriesData);
      
      // Ensure it's an array
      if (Array.isArray(memoriesData)) {
        setMemories(memoriesData);
      } else {
        console.warn('Memories is not an array:', memoriesData);
        setMemories([]);
      }
    } catch (error) {
      console.error('❌ Error loading memories:', error.message);
      setMemories([]); // Set to empty array on error
    }
  }, [userId]);

  // Show snackbar notification
  const showSnackbar = useCallback((message, severity) => {
    setSnackbar({ open: true, message, severity });
  }, []);

  // Close snackbar
  const handleCloseSnackbar = useCallback(() => {
    setSnackbar(prev => ({ ...prev, open: false }));
  }, []);

  // Initialize app
  useEffect(() => {
    const initializeApp = async () => {
      await checkApiStatus();
      await loadUserInfo();
      await loadMemories();
    };
    initializeApp();
  }, [checkApiStatus, loadUserInfo, loadMemories]);

  // Debug memories state
  useEffect(() => {
    console.log('💾 Memories state updated:', memories);
    console.log('💾 Memories is array?', Array.isArray(memories));
    console.log('💾 Memories length:', memories?.length || 0);
  }, [memories]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  // Send message to backend - FIXED WITH async
  const sendMessage = async () => {
    if (!input.trim() || loading || apiStatus !== 'connected') return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message to UI
    const newUserMessage = {
      id: Date.now(),
      text: userMessage,
      sender: 'user',
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, newUserMessage]);
    setLoading(true);
    setTyping(true);

    try {
      // Send to backend
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        user_id: userId,
        message: userMessage,
        session_id: sessionId
      });

      const data = response.data;

      // Update session ID if needed
      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }

      // Add bot response
      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        sender: 'bot',
        emotion: data.emotion_detected,
        timestamp: data.timestamp,
        tone: data.tone,
        modelUsed: data.model_used,
        memoriesUsed: data.memories_used
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Refresh data
      loadUserInfo();
      loadMemories();
      
      showSnackbar('Response received', 'success');
      
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: "I'm having trouble connecting to the backend. Please make sure the server is running on http://localhost:8007",
        sender: 'bot',
        emotion: 'sadness',
        timestamp: new Date().toISOString(),
        isError: true
      }]);
      showSnackbar('Error connecting to backend', 'error');
    } finally {
      setLoading(false);
      setTyping(false);
    }
  };

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Create new user session
  const createNewUser = () => {
    const newUserId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setUserId(newUserId);
    localStorage.setItem('empathai_user_id', newUserId);
    setMessages([]);
    setSessionId(null);
    setMemories([]);
    setUserInfo(null);
    showSnackbar('New user session created', 'info');
  };

  // Clear conversation
  const clearConversation = () => {
    setMessages([]);
    setSessionId(null);
    showSnackbar('Conversation cleared', 'info');
  };

  // Delete memory
  const deleteMemory = async (memoryId) => {
    showSnackbar('Memory deletion not implemented in this version', 'warning');
  };

  // Quick prompts
  const quickPrompts = [
    { text: "Tell me about yourself", icon: <InfoIcon /> },
    { text: "How do you remember things?", icon: <MemoryIcon /> },
    { text: "I'm feeling happy today!", icon: <HappyIcon /> },
    { text: "What's your favorite memory?", icon: <HistoryIcon /> },
    { text: "Can you detect my emotions?", icon: <PsychologyIcon /> },
  ];

  // Safe memories getter
  const getSafeMemories = () => {
    if (!memories) return [];
    if (!Array.isArray(memories)) return [];
    return memories;
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
        {/* Notification Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={4000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>

        {/* Sidebar Drawer */}
        <Drawer
          variant="temporary"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          sx={{
            '& .MuiDrawer-paper': {
              width: 350,
              bgcolor: 'background.paper',
              borderRight: '1px solid',
              borderColor: 'divider',
            },
          }}
        >
          <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'primary.main' }}>
              <PsychologyIcon /> Dashboard
            </Typography>
            <IconButton onClick={() => setDrawerOpen(false)} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
          <Divider />
          
          {/* Connection Status */}
          <Box sx={{ p: 2 }}>
            <Card sx={{ bgcolor: apiStatus === 'connected' ? 'success.dark' : 'error.dark' }}>
              <CardContent sx={{ py: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="subtitle2" sx={{ color: 'white' }}>
                      Backend Status
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      {apiStatus === 'connected' ? 'Connected' : 'Disconnected'}
                    </Typography>
                  </Box>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={checkApiStatus}
                    sx={{ bgcolor: 'white', color: 'black', '&:hover': { bgcolor: '#f1f5f9' } }}
                  >
                    Check
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* User Profile */}
          <Box sx={{ p: 2 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
                    <PersonIcon />
                  </Avatar>
                  <Box>
                    <Typography variant="h6">User Profile</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                      {userId.substring(0, 16)}...
                    </Typography>
                  </Box>
                </Box>
                
                {userInfo && (
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: 'primary.dark' }}>
                        <Typography variant="h4" color="white">{userInfo.total_conversations || 0}</Typography>
                        <Typography variant="caption" color="rgba(255,255,255,0.8)">Conversations</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6}>
                      <Paper sx={{ p: 1.5, textAlign: 'center', bgcolor: 'secondary.dark' }}>
                        <Typography variant="h4" color="white">{userInfo.memory_count || 0}</Typography>
                        <Typography variant="caption" color="rgba(255,255,255,0.8)">Memories</Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                )}

                <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={createNewUser}
                    startIcon={<RefreshIcon />}
                    size="small"
                  >
                    New Session
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    onClick={clearConversation}
                    startIcon={<DeleteIcon />}
                    size="small"
                    color="error"
                  >
                    Clear Chat
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>

          {/* Memories Section - FIXED WITH SAFE ACCESS */}
          <Box sx={{ p: 2, flex: 1, overflow: 'auto' }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <MemoryIcon /> Recent Memories
            </Typography>
            
            {getSafeMemories().length > 0 ? (
              <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
                {getSafeMemories().slice(0, 5).map((memory, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <ListItem
                      sx={{
                        mb: 1,
                        bgcolor: 'background.default',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        {memory?.memory_type === 'preference' ? (
                          <LoveIcon color="error" />
                        ) : memory?.memory_type === 'fact' ? (
                          <InfoIcon color="info" />
                        ) : (
                          <HistoryIcon color="warning" />
                        )}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                            {memory?.content && memory.content.length > 60 
                              ? memory.content.substring(0, 60) + '...' 
                              : memory?.content || 'Memory content'}
                          </Typography>
                        }
                        secondary={
                          <Typography variant="caption" color="text.secondary">
                            {memory?.memory_type || 'conversation'} • {format(
                              new Date(memory?.timestamp || Date.now()), 
                              'MMM d, HH:mm'
                            )}
                          </Typography>
                        }
                      />
                      <IconButton size="small" onClick={() => deleteMemory(memory?.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </ListItem>
                  </motion.div>
                ))}
              </List>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <MemoryIcon sx={{ fontSize: 48, color: 'text.secondary', opacity: 0.5, mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  No memories yet. Start chatting to create memories!
                </Typography>
              </Box>
            )}
          </Box>
        </Drawer>

        {/* Main Content */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Top App Bar */}
          <AppBar position="static" color="transparent" elevation={1}>
            <Toolbar>
              <IconButton
                edge="start"
                color="inherit"
                onClick={() => setDrawerOpen(true)}
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ repeat: Infinity, duration: 3 }}
                >
                  <BotIcon sx={{ fontSize: 32, color: 'primary.main' }} />
                </motion.div>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    EmpathAI Companion
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Emotional Intelligence & Long-term Memory
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  icon={<PsychologyIcon />}
                  label="Emotion AI"
                  size="small"
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  icon={<MemoryIcon />}
                  label="Memory"
                  size="small"
                  color="secondary"
                  variant="outlined"
                />
                <Chip
                  icon={<BotIcon />}
                  label={apiStatus === 'connected' ? 'Connected' : 'Offline'}
                  size="small"
                  color={apiStatus === 'connected' ? 'success' : 'error'}
                  variant="outlined"
                />
              </Box>
            </Toolbar>
          </AppBar>

          {/* Chat Container */}
          <Container maxWidth="lg" sx={{ flex: 1, display: 'flex', flexDirection: 'column', py: 3 }}>
            <Paper
              elevation={0}
              sx={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                bgcolor: 'background.paper',
                borderRadius: 3,
                overflow: 'hidden',
                border: '1px solid',
                borderColor: 'divider',
              }}
            >
              {/* Messages Area */}
              <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
                {messages.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 8, px: 2 }}>
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 200, damping: 15 }}
                    >
                      <Box sx={{ position: 'relative', display: 'inline-block', mb: 4 }}>
                        <Avatar
                          sx={{
                            width: 120,
                            height: 120,
                            bgcolor: 'primary.main',
                            mb: 2,
                          }}
                        >
                          <BotIcon sx={{ fontSize: 60 }} />
                        </Avatar>
                        <Box
                          sx={{
                            position: 'absolute',
                            bottom: 0,
                            right: 0,
                            bgcolor: 'success.main',
                            borderRadius: '50%',
                            width: 32,
                            height: 32,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '3px solid',
                            borderColor: 'background.paper',
                          }}
                        >
                          <PsychologyIcon sx={{ fontSize: 16, color: 'white' }} />
                        </Box>
                      </Box>
                    </motion.div>
                    
                    <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, mb: 2 }}>
                      Hello! I'm Alex 🤖
                    </Typography>
                    
                    <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600, mx: 'auto', mb: 4 }}>
                      I'm your empathetic AI companion. I can remember our conversations, 
                      understand your emotions, and adapt my responses to make our chats more meaningful.
                    </Typography>

                    <Grid container spacing={2} justifyContent="center" sx={{ mb: 4 }}>
                      {quickPrompts.map((prompt, index) => (
                        <Grid item key={index}>
                          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                            <Chip
                              icon={prompt.icon}
                              label={prompt.text}
                              onClick={() => setInput(prompt.text)}
                              sx={{
                                cursor: 'pointer',
                                bgcolor: 'primary.dark',
                                color: 'white',
                                '&:hover': { bgcolor: 'primary.main' }
                              }}
                            />
                          </motion.div>
                        </Grid>
                      ))}
                    </Grid>

                    <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: 'primary.light', width: 56, height: 56, mx: 'auto', mb: 1 }}>
                          <PsychologyIcon />
                        </Avatar>
                        <Typography variant="caption">Emotion Detection</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: 'secondary.light', width: 56, height: 56, mx: 'auto', mb: 1 }}>
                          <MemoryIcon />
                        </Avatar>
                        <Typography variant="caption">Long-term Memory</Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: 'success.light', width: 56, height: 56, mx: 'auto', mb: 1 }}>
                          <SettingsIcon />
                        </Avatar>
                        <Typography variant="caption">Adaptive Tone</Typography>
                      </Box>
                    </Box>
                  </Box>
                ) : (
                  <>
                    {messages.map((message, index) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                            mb: 3,
                          }}
                        >
                          <Box
                            sx={{
                              display: 'flex',
                              flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                              alignItems: 'flex-start',
                              gap: 2,
                              maxWidth: '80%',
                            }}
                          >
                            <Avatar
                              sx={{
                                bgcolor: message.sender === 'user' ? 'primary.main' : 'secondary.main',
                                width: 40,
                                height: 40,
                              }}
                            >
                              {message.sender === 'user' ? <PersonIcon /> : <BotIcon />}
                            </Avatar>
                            
                            <Box sx={{ maxWidth: '100%' }}>
                              <Paper
                                sx={{
                                  p: 2.5,
                                  bgcolor: message.sender === 'user' ? 'primary.main' : 'background.default',
                                  color: message.sender === 'user' ? 'white' : 'text.primary',
                                  borderRadius: 3,
                                  borderTopLeftRadius: message.sender === 'user' ? 20 : 8,
                                  borderTopRightRadius: message.sender === 'user' ? 8 : 20,
                                  boxShadow: 1,
                                }}
                              >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.5 }}>
                                  {message.emotion && message.sender === 'bot' && emotionConfig[message.emotion] && (
                                    <Tooltip title={`Detected: ${emotionConfig[message.emotion].label}`}>
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                        {emotionConfig[message.emotion].icon}
                                        <Typography variant="caption" sx={{ opacity: 0.8 }}>
                                          {emotionConfig[message.emotion].label}
                                        </Typography>
                                      </Box>
                                    </Tooltip>
                                  )}
                                  
                                  {message.memoriesUsed && message.sender === 'bot' && (
                                    <Tooltip title="Using memories from previous conversations">
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1 }}>
                                        <MemoryIcon fontSize="small" color="secondary" />
                                        <Typography variant="caption" color="text.secondary">
                                          Memory
                                        </Typography>
                                      </Box>
                                    </Tooltip>
                                  )}
                                  
                                  <Typography 
                                    variant="caption" 
                                    sx={{ 
                                      ml: 'auto', 
                                      opacity: 0.7,
                                      color: message.sender === 'user' ? 'rgba(255,255,255,0.7)' : 'inherit'
                                    }}
                                  >
                                    {format(new Date(message.timestamp), 'HH:mm')}
                                  </Typography>
                                </Box>
                                
                                <ReactMarkdown
                                  components={{
                                    p: ({ children }) => (
                                      <Typography 
                                        sx={{ 
                                          whiteSpace: 'pre-wrap',
                                          lineHeight: 1.6,
                                          color: message.sender === 'user' ? 'white' : 'inherit'
                                        }}
                                      >
                                        {children}
                                      </Typography>
                                    ),
                                    strong: ({ children }) => (
                                      <span style={{ 
                                        fontWeight: 700,
                                        color: message.sender === 'user' ? 'white' : 'primary.light'
                                      }}>
                                        {children}
                                      </span>
                                    ),
                                    em: ({ children }) => (
                                      <span style={{ fontStyle: 'italic' }}>
                                        {children}
                                      </span>
                                    ),
                                  }}
                                >
                                  {message.text}
                                </ReactMarkdown>
                              </Paper>
                              
                              {message.tone && message.sender === 'bot' && (
                                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block', pl: 1 }}>
                                  Tone: {message.tone}
                                </Typography>
                              )}
                            </Box>
                          </Box>
                        </Box>
                      </motion.div>
                    ))}
                    
                    {typing && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                      >
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                          <Avatar sx={{ bgcolor: 'secondary.main', width: 40, height: 40 }}>
                            <BotIcon />
                          </Avatar>
                          <Paper sx={{ p: 2, borderRadius: 3, bgcolor: 'background.default' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                              <CircularProgress size={20} thickness={4} />
                              <Typography variant="body2" color="text.secondary">
                                Alex is thinking...
                              </Typography>
                              <Box sx={{ display: 'flex', gap: 0.5 }}>
                                {[0, 1, 2].map(i => (
                                  <motion.div
                                    key={i}
                                    animate={{ y: [0, -5, 0] }}
                                    transition={{ repeat: Infinity, duration: 1, delay: i * 0.2 }}
                                  >
                                    <Box sx={{ width: 4, height: 4, borderRadius: '50%', bgcolor: 'secondary.main' }} />
                                  </motion.div>
                                ))}
                              </Box>
                            </Box>
                          </Paper>
                        </Box>
                      </motion.div>
                    )}
                    
                    <div ref={messagesEndRef} />
                  </>
                )}
              </Box>

              {/* Input Area */}
              <Box sx={{ p: 3, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'background.default' }}>
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
                  <TextField
                    fullWidth
                    multiline
                    maxRows={4}
                    minRows={1}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={
                      apiStatus === 'connected' 
                        ? "Type your message here... (Press Enter to send, Shift+Enter for new line)" 
                        : "Backend not connected. Please start the server first."
                    }
                    variant="outlined"
                    size="medium"
                    disabled={loading || apiStatus !== 'connected'}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        bgcolor: 'background.paper',
                        '&:hover': {
                          '& .MuiOutlinedInput-notchedOutline': {
                            borderColor: 'primary.main',
                          },
                        },
                      },
                    }}
                    InputProps={{
                      endAdornment: (
                        <Typography variant="caption" color="text.secondary">
                          {input.length}/2000
                        </Typography>
                      ),
                    }}
                  />
                  
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button
                      variant="contained"
                      onClick={sendMessage}
                      disabled={loading || !input.trim() || apiStatus !== 'connected'}
                      sx={{
                        borderRadius: 2,
                        minWidth: 56,
                        height: 56,
                        bgcolor: 'primary.main',
                        '&:hover': { bgcolor: 'primary.dark' },
                        '&.Mui-disabled': { bgcolor: 'action.disabledBackground' }
                      }}
                    >
                      {loading ? (
                        <CircularProgress size={24} sx={{ color: 'white' }} />
                      ) : (
                        <SendIcon sx={{ fontSize: 24 }} />
                      )}
                    </Button>
                  </motion.div>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1.5, px: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {apiStatus === 'connected' ? '✅ Backend connected' : '❌ Backend disconnected'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Session: {sessionId ? `${sessionId.substring(0, 8)}...` : 'New'}
                  </Typography>
                </Box>
              </Box>
            </Paper>

            {/* Quick Stats Footer - FIXED WITH SAFE ACCESS */}
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3, gap: 3 }}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="primary.main">
                  {messages.filter(m => m.sender === 'user').length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Your Messages
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="secondary.main">
                  {getSafeMemories().length} {/* Safe access */}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Stored Memories
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h6" color="success.main">
                  {messages.filter(m => m.emotion).length}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Emotions Detected
                </Typography>
              </Box>
            </Box>
          </Container>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;