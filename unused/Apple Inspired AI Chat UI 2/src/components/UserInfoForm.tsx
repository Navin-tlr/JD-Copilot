import { useState } from 'react';
import { motion } from 'motion/react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ArrowLeft, ArrowRight } from 'lucide-react';

interface UserInfoFormProps {
  onContinue: (userInfo: UserInfo) => void;
  onBack: () => void;
}

export interface UserInfo {
  firstName: string;
  lastName: string;
  yearOfStudy: string;
  campus: string;
}

export function UserInfoForm({ onContinue, onBack }: UserInfoFormProps) {
  const [userInfo, setUserInfo] = useState<UserInfo>({
    firstName: '',
    lastName: '',
    yearOfStudy: '',
    campus: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  const isFormValid = userInfo.firstName && userInfo.lastName && userInfo.yearOfStudy && userInfo.campus;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormValid) return;

    setIsLoading(true);
    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
    onContinue(userInfo);
  };

  const updateUserInfo = (field: keyof UserInfo, value: string) => {
    setUserInfo(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-center justify-between p-4 border-b border-border/50"
      >
        <Button
          variant="ghost"
          size="icon"
          onClick={onBack}
          className="h-10 w-10 rounded-full"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="text-lg font-medium">Create Account</h1>
        <div className="w-10"></div>
      </motion.div>

      {/* Form */}
      <div className="flex-1 px-6 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-md mx-auto"
        >
          <div className="text-center mb-8">
            <h2 className="text-2xl font-medium mb-2">Tell us about yourself</h2>
            <p className="text-muted-foreground">We'll use this to personalize your experience</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* First Name */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="space-y-2"
            >
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                type="text"
                placeholder="Enter your first name"
                value={userInfo.firstName}
                onChange={(e) => updateUserInfo('firstName', e.target.value)}
                className="h-12 rounded-xl"
              />
            </motion.div>

            {/* Last Name */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="space-y-2"
            >
              <Label htmlFor="lastName">Last Name</Label>
              <Input
                id="lastName"
                type="text"
                placeholder="Enter your last name"
                value={userInfo.lastName}
                onChange={(e) => updateUserInfo('lastName', e.target.value)}
                className="h-12 rounded-xl"
              />
            </motion.div>

            {/* Year of Study */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="space-y-2"
            >
              <Label>Year of Study</Label>
              <Select onValueChange={(value) => updateUserInfo('yearOfStudy', value)}>
                <SelectTrigger className="h-12 rounded-xl">
                  <SelectValue placeholder="Select your year" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1st-year">1st Year</SelectItem>
                  <SelectItem value="2nd-year">2nd Year</SelectItem>
                  <SelectItem value="3rd-year">3rd Year</SelectItem>
                  <SelectItem value="4th-year">4th Year</SelectItem>
                  <SelectItem value="masters">Master's</SelectItem>
                  <SelectItem value="phd">PhD</SelectItem>
                  <SelectItem value="postdoc">Postdoc</SelectItem>
                </SelectContent>
              </Select>
            </motion.div>

            {/* Campus */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="space-y-2"
            >
              <Label>Campus</Label>
              <Select onValueChange={(value) => updateUserInfo('campus', value)}>
                <SelectTrigger className="h-12 rounded-xl">
                  <SelectValue placeholder="Select your campus" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="main-campus">Main Campus</SelectItem>
                  <SelectItem value="north-campus">North Campus</SelectItem>
                  <SelectItem value="south-campus">South Campus</SelectItem>
                  <SelectItem value="east-campus">East Campus</SelectItem>
                  <SelectItem value="west-campus">West Campus</SelectItem>
                  <SelectItem value="downtown">Downtown Campus</SelectItem>
                  <SelectItem value="online">Online</SelectItem>
                </SelectContent>
              </Select>
            </motion.div>

            {/* Continue Button */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.5 }}
              className="pt-4"
            >
              <Button
                type="submit"
                disabled={!isFormValid || isLoading}
                className="w-full h-14 rounded-xl text-base font-medium"
              >
                {isLoading ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-5 h-5 border-2 border-primary-foreground border-t-transparent rounded-full"
                  />
                ) : (
                  <>
                    Continue
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </>
                )}
              </Button>
            </motion.div>
          </form>
        </motion.div>
      </div>
    </div>
  );
}