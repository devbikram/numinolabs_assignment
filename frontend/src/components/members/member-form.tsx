"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import type { Member } from "@/types";
import { useCreateMember, useUpdateMember } from "@/lib/queries/members";
import { FormDialog } from "@/components/ui/form-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FormFooter } from "@/components/ui/form-footer";
import { FieldErrorMsg } from "@/components/ui/field-error";
import { toastError } from "@/lib/errors";
import { toast } from "sonner";

const memberSchema = z.object({
  full_name: z.string().min(1, "Name is required").max(255, "Max 255 characters"),
  email: z.string().email("Invalid email"),
  phone: z.string().max(20, "Max 20 characters").regex(/^(?:\+?[\d\s\-().]{7,20})?$/, "Invalid phone format (min 7 digits)").optional(),
  address: z.string().max(256, "Max 256 characters").optional(),
});

type MemberFormData = z.infer<typeof memberSchema>;

interface MemberFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member?: Member;
}

export function MemberForm({ open, onOpenChange, member }: MemberFormProps) {
  const createMember = useCreateMember();
  const updateMember = useUpdateMember();
  const isEdit = !!member;

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<MemberFormData>({
    resolver: zodResolver(memberSchema),
  });

  useEffect(() => {
    if (open) {
      reset(
        member
          ? {
              full_name: member.full_name,
              email: member.email,
              phone: member.phone ?? "",
              address: member.address ?? "",
            }
          : { full_name: "", email: "", phone: "", address: "" }
      );
    }
  }, [open, member, reset]);

  async function onSubmit(data: MemberFormData) {
    try {
      const payload = {
        ...data,
        phone: data.phone || null,
        address: data.address || null,
      };
      if (isEdit) {
        await updateMember.mutateAsync({ id: member.id, data: payload });
        toast.success("Member updated");
      } else {
        await createMember.mutateAsync(payload);
        toast.success("Member created");
      }
      onOpenChange(false);
    } catch (e) {
      toastError(e);
    }
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit Member" : "Add Member"}
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className="space-y-1">
        <Label htmlFor="full_name">Full Name</Label>
        <Input id="full_name" {...register("full_name")} />
        <FieldErrorMsg error={errors.full_name} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" {...register("email")} />
        <FieldErrorMsg error={errors.email} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="phone">Phone</Label>
        <Input id="phone" {...register("phone")} />
      </div>
      <div className="space-y-1">
        <Label htmlFor="address">Address</Label>
        <Input id="address" {...register("address")} />
      </div>
      <FormFooter
        isSubmitting={isSubmitting}
        isEdit={isEdit}
        onCancel={() => onOpenChange(false)}
      />
    </FormDialog>
  );
}
