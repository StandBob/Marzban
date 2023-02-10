import { fetch } from "service/http";
import { mutate as globalMutate } from "swr";
import { User, UserCreate } from "types/User";
import { create } from "zustand";
import { computed } from "zustand-computed";

export type FilterType = {
  search: string;
};

type ComputedStore = {
  filteredUsers: User[];
};

type DashboardStateType = {
  isCreatingNewUser: boolean;
  editingUser: User | null | undefined;
  deletingUser: User | null;
  users: User[];
  loading: boolean;
  filters: FilterType;
  QRcodeLinks: string[] | null;
  isEditingHosts: boolean;
  onCreateUser: (isOpen: boolean) => void;
  onEditingUser: (user: User | null) => void;
  onDeletingUser: (user: User | null) => void;
  refetchUsers: () => void;
  onFilterChange: (filters: FilterType) => void;
  deleteUser: (user: User) => Promise<void>;
  createUser: (user: UserCreate) => Promise<void>;
  editUser: (user: UserCreate) => Promise<void>;
  setQRCode: (links: string[] | null) => void;
  onEditingHosts: (isEditingHosts: boolean) => void;
};

const fetchUsers = (query: FilterType): Promise<User[]> => {
  useDashboard.setState({ loading: true });
  return fetch("/users", { query })
    .then((users) => {
      useDashboard.setState({ users });
      return users;
    })
    .finally(() => {
      useDashboard.setState({ loading: false });
    });
};

export const useDashboard = create<
  DashboardStateType,
  [["chrisvander/zustand-computed", ComputedStore]]
>(
  computed(
    (set, get) => ({
      editingUser: null,
      deletingUser: null,
      isCreatingNewUser: false,
      QRcodeLinks: null,
      users: [],
      loading: true,
      isEditingHosts: false,
      filters: { search: "" },
      refetchUsers: () => {
        fetchUsers(get().filters);
      },
      onCreateUser: (isCreatingNewUser) => set({ isCreatingNewUser }),
      onEditingUser: (editingUser) => {
        set({ editingUser });
      },
      onDeletingUser: (deletingUser) => {
        set({ deletingUser });
      },
      onFilterChange: (filters) => {
        set({ filters });
      },
      setQRCode: (QRcodeLinks) => {
        set({ QRcodeLinks });
      },
      deleteUser: (user: User) => {
        set({ editingUser: null });
        return fetch(`/user/${user.username}`, { method: "DELETE" }).then(
          () => {
            set({ deletingUser: null });
            get().refetchUsers();
            globalMutate("/system");
          }
        );
      },
      createUser: (body: UserCreate) => {
        return fetch(`/user`, { method: "POST", body }).then(() => {
          set({ editingUser: null });
          get().refetchUsers();
          globalMutate("/system");
        });
      },
      editUser: (body: UserCreate) => {
        return fetch(`/user/${body.username}`, { method: "PUT", body }).then(
          () => {
            set({ editingUser: null });
            get().refetchUsers();
          }
        );
      },
      onEditingHosts: (isEditingHosts: boolean) => {
        set({ isEditingHosts });
      },
    }),
    (state): ComputedStore => {
      return {
        filteredUsers: state.users.filter(
          (user) => user.username.indexOf(state.filters.search) > -1
        ),
      };
    }
  )
);

fetchUsers(useDashboard.getState().filters);
