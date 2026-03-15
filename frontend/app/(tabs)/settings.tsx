import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/auth';
import { colors, spacing, radius } from '../../src/theme';

const c = colors.light;

export default function SettingsScreen() {
  const router = useRouter();
  const { user, logout } = useAuth();

  async function handleLogout() {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Logout', style: 'destructive', onPress: async () => { await logout(); router.replace('/(auth)/login'); } },
    ]);
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>Settings</Text>

        {/* Profile Section */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>{user?.name?.charAt(0) || 'D'}</Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{user?.name}</Text>
            <Text style={styles.profileEmail}>{user?.email}</Text>
            <View style={styles.roleBadge}>
              <Text style={styles.roleText}>{user?.role || 'Doctor'}</Text>
            </View>
          </View>
        </View>

        {/* Clinic Management */}
        <Text style={styles.sectionTitle}>Clinic Management</Text>
        <View style={styles.menuCard}>
          <MenuItem testID="settings-clinic-info" icon="business-outline" label="Clinic Information" onPress={() => router.push('/(tabs)/clinic')} />
          <MenuItem testID="settings-clinic-hours" icon="time-outline" label="Clinic Hours" onPress={() => router.push('/clinic-hours')} />
          <MenuItem testID="settings-patients" icon="people-outline" label="Patients" onPress={() => router.push('/patients')} />
          <MenuItem testID="settings-calendar" icon="calendar-outline" label="Appointment Calendar" onPress={() => router.push('/calendar')} />
        </View>

        {/* AI Agent */}
        <Text style={styles.sectionTitle}>AI Agent</Text>
        <View style={styles.menuCard}>
          <MenuItem testID="settings-ai-config" icon="pulse-outline" label="AI Agent Configuration" onPress={() => router.push('/ai-config')} />
          <MenuItem testID="settings-test-ai" icon="chatbubble-ellipses-outline" label="Test AI Agent (Simulate Call)" onPress={() => router.push('/simulate-chat')} />
        </View>

        {/* Integrations */}
        <Text style={styles.sectionTitle}>Integrations</Text>
        <View style={styles.menuCard}>
          <View style={styles.menuItem}>
            <View style={[styles.menuIconWrap, { backgroundColor: '#25D36620' }]}>
              <Ionicons name="logo-whatsapp" size={20} color="#25D366" />
            </View>
            <Text style={styles.menuLabel}>WhatsApp (Twilio)</Text>
            <View style={[styles.connectedBadge, { backgroundColor: c.warning + '20' }]}>
              <Text style={{ fontSize: 12, color: c.warning, fontWeight: '600' }}>Configure in .env</Text>
            </View>
          </View>
        </View>

        {/* Account */}
        <Text style={styles.sectionTitle}>Account</Text>
        <View style={styles.menuCard}>
          <TouchableOpacity testID="logout-btn" style={styles.menuItem} onPress={handleLogout}>
            <View style={[styles.menuIconWrap, { backgroundColor: c.accent + '15' }]}>
              <Ionicons name="log-out-outline" size={20} color={c.accent} />
            </View>
            <Text style={[styles.menuLabel, { color: c.accent }]}>Logout</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.version}>DentalAI v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function MenuItem({ testID, icon, label, onPress }: any) {
  return (
    <TouchableOpacity testID={testID} style={styles.menuItem} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.menuIconWrap}>
        <Ionicons name={icon} size={20} color={c.primary} />
      </View>
      <Text style={styles.menuLabel}>{label}</Text>
      <Ionicons name="chevron-forward" size={18} color={c.textMuted} />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: c.background },
  scroll: { paddingHorizontal: spacing.xl, paddingBottom: 100 },
  title: { fontSize: 28, fontWeight: '700', color: c.textMain, paddingTop: spacing.lg, paddingBottom: spacing.xl },
  profileCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: c.surface, borderRadius: radius.lg, padding: spacing.xl, marginBottom: spacing.xxl, borderWidth: 1, borderColor: c.border },
  avatar: { width: 56, height: 56, borderRadius: 28, backgroundColor: c.primary, alignItems: 'center', justifyContent: 'center', marginRight: spacing.lg },
  avatarText: { fontSize: 24, fontWeight: '700', color: '#FFF' },
  profileInfo: { flex: 1 },
  profileName: { fontSize: 18, fontWeight: '600', color: c.textMain },
  profileEmail: { fontSize: 14, color: c.textMuted, marginTop: 2 },
  roleBadge: { marginTop: spacing.sm, backgroundColor: c.secondary, borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 2, alignSelf: 'flex-start' },
  roleText: { fontSize: 12, color: c.primary, fontWeight: '600', textTransform: 'capitalize' },
  sectionTitle: { fontSize: 14, fontWeight: '600', color: c.textMuted, marginBottom: spacing.md, textTransform: 'uppercase', letterSpacing: 0.5 },
  menuCard: { backgroundColor: c.surface, borderRadius: radius.lg, marginBottom: spacing.xxl, borderWidth: 1, borderColor: c.border, overflow: 'hidden' },
  menuItem: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, paddingVertical: spacing.lg, borderBottomWidth: 1, borderBottomColor: c.border },
  menuIconWrap: { width: 36, height: 36, borderRadius: radius.md, backgroundColor: c.secondary, alignItems: 'center', justifyContent: 'center', marginRight: spacing.md },
  menuLabel: { flex: 1, fontSize: 16, fontWeight: '500', color: c.textMain },
  connectedBadge: { borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 4 },
  version: { textAlign: 'center', color: c.textMuted, fontSize: 13, marginTop: spacing.lg },
});
