import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/auth';
import { api } from '../../src/api';
import { colors, spacing, radius } from '../../src/theme';

const c = colors.light;

export default function LoginScreen() {
  const router = useRouter();
  const { login, user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (user) router.replace('/(tabs)');
  }, [user]);

  async function handleLogin() {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    setLoading(true);
    try {
      const res = await api.login({ email: email.trim().toLowerCase(), password });
      await login(res.token, res.user);
      router.replace('/(tabs)');
    } catch (e: any) {
      Alert.alert('Login Failed', e.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.flex}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.heroSection}>
            <View style={styles.iconCircle}>
              <Ionicons name="medical" size={40} color={c.primary} />
            </View>
            <Text style={styles.appName}>DentalAI</Text>
            <Text style={styles.tagline}>Smart Receptionist for Your Clinic</Text>
          </View>

          <View style={styles.formCard}>
            <Text style={styles.formTitle}>Welcome Back</Text>
            <Text style={styles.formSubtitle}>Sign in to manage your clinic</Text>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Email</Text>
              <View style={styles.inputWrapper}>
                <Ionicons name="mail-outline" size={20} color={c.textMuted} style={styles.inputIcon} />
                <TextInput
                  testID="login-email-input"
                  style={styles.input}
                  placeholder="dr.sharma@dental.com"
                  placeholderTextColor={c.textMuted}
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Password</Text>
              <View style={styles.inputWrapper}>
                <Ionicons name="lock-closed-outline" size={20} color={c.textMuted} style={styles.inputIcon} />
                <TextInput
                  testID="login-password-input"
                  style={styles.input}
                  placeholder="Enter password"
                  placeholderTextColor={c.textMuted}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry={!showPassword}
                />
                <TouchableOpacity testID="toggle-password-btn" onPress={() => setShowPassword(!showPassword)} style={styles.eyeBtn}>
                  <Ionicons name={showPassword ? 'eye-off-outline' : 'eye-outline'} size={20} color={c.textMuted} />
                </TouchableOpacity>
              </View>
            </View>

            <TouchableOpacity testID="login-submit-btn" style={styles.primaryBtn} onPress={handleLogin} disabled={loading} activeOpacity={0.8}>
              {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.primaryBtnText}>Sign In</Text>}
            </TouchableOpacity>

            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.dividerLine} />
            </View>

            <TouchableOpacity testID="go-register-btn" style={styles.secondaryBtn} onPress={() => router.push('/(auth)/register')} activeOpacity={0.7}>
              <Text style={styles.secondaryBtnText}>Create New Account</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.footer}>Seed login: dr.sharma@dental.com / password123</Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: c.background },
  flex: { flex: 1 },
  scroll: { flexGrow: 1, paddingHorizontal: spacing.xl, paddingBottom: spacing.xxxl },
  heroSection: { alignItems: 'center', paddingTop: spacing.xxxl, paddingBottom: spacing.xxl },
  iconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.lg },
  appName: { fontSize: 32, fontWeight: '700', color: c.primary, letterSpacing: -0.5 },
  tagline: { fontSize: 16, color: c.textMuted, marginTop: spacing.xs },
  formCard: { backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 12, elevation: 3 },
  formTitle: { fontSize: 24, fontWeight: '600', color: c.textMain, marginBottom: spacing.xs },
  formSubtitle: { fontSize: 14, color: c.textMuted, marginBottom: spacing.xl },
  inputGroup: { marginBottom: spacing.lg },
  label: { fontSize: 14, fontWeight: '500', color: c.textMuted, marginBottom: spacing.sm },
  inputWrapper: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.background, borderRadius: radius.md, borderWidth: 1, borderColor: c.border, paddingHorizontal: spacing.md },
  inputIcon: { marginRight: spacing.sm },
  input: { flex: 1, paddingVertical: 14, fontSize: 16, color: c.textMain },
  eyeBtn: { padding: spacing.sm },
  primaryBtn: { backgroundColor: c.primary, borderRadius: radius.full, paddingVertical: 16, alignItems: 'center', marginTop: spacing.lg },
  primaryBtnText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
  divider: { flexDirection: 'row', alignItems: 'center', marginVertical: spacing.xl },
  dividerLine: { flex: 1, height: 1, backgroundColor: c.border },
  dividerText: { marginHorizontal: spacing.lg, color: c.textMuted, fontSize: 14 },
  secondaryBtn: { borderWidth: 1.5, borderColor: c.primary, borderRadius: radius.full, paddingVertical: 14, alignItems: 'center' },
  secondaryBtnText: { color: c.primary, fontSize: 16, fontWeight: '600' },
  footer: { textAlign: 'center', color: c.textMuted, fontSize: 12, marginTop: spacing.xl },
});
